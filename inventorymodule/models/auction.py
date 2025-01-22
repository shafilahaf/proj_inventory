from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import base64

class aeAuctionHeader(models.Model):
    _name = 'ae.auction.header'
    _description = 'Auction Report Header'
    _rec_name = 'document_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'posting_date desc'

    cost_centre = fields.Char(string="Cost Centre")
    internal_order = fields.Char(string="Internal Order")
    active = fields.Boolean(default=True)
    document_no = fields.Char(string='Document No', required=True, readonly=True, default='New')
    posting_date = fields.Datetime(string='Posting Date', required=True, default=fields.Datetime.now)
    auction_date = fields.Date(string='Auction Date', required=True)
    auction_date_char = fields.Char(string='Auction Date Char', compute='_compute_auction_date_char')
    location_name = fields.Many2one('ae.location', string='Location Name')
    fee = fields.Integer(string='Fee %',min = 0,max= 100)
    agency_name = fields.Many2one('ae.master.agency', string='Agency Name', required=True)
    ppn = fields.Integer(string='PPN %',min = 0,max= 100)

    lot_no = fields.Char(string='Lot No', size=20, required=True)
    auction_group = fields.Char(string='Auction Group', size=50)

    harga_limit = fields.Integer(string='Harga Limit')
    harga_terbentuk = fields.Integer(string='Harga Terbentuk')
    status = fields.Selection([
        ('open', 'Open'),
        ('posted', 'Posted'),
    ], string='Status', required=True, default='open')
   
    auction_line_ids = fields.One2many('ae.auction.line', 'auction_header_id', string='Auction Lines')
    auction_file_attach = fields.Binary(string='Attachment')
    fee_hargaterbentuk = fields.Integer(string='Fee Harga Terbentuk', compute='_compute_fee_hargaterbentuk')
    ppn_feehargaterbentuk = fields.Integer(string='PPN Fee Harga Terbentuk', compute='_compute_ppn_feehargaterbentuk')
    total = fields.Integer(string='Total', compute='_compute_total')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id.id)

    # Section function
    def action_print_auction_report(self):
        """
        This function is used to print auction report
        """
        return self.env.ref('inventorymodule.action_report_auction').report_action(self)

    @api.depends('fee_hargaterbentuk','ppn_feehargaterbentuk','harga_terbentuk')
    def _compute_total(self):
        for record in self:
            record.total = record.harga_terbentuk - record.fee_hargaterbentuk - record.ppn_feehargaterbentuk

    @api.depends('fee_hargaterbentuk','ppn')
    def _compute_ppn_feehargaterbentuk(self):
        for record in self:
            record.ppn_feehargaterbentuk = record.fee_hargaterbentuk * record.ppn / 100

    @api.depends('harga_terbentuk','fee')
    def _compute_fee_hargaterbentuk(self):
        for record in self:
            record.fee_hargaterbentuk = record.harga_terbentuk * record.fee / 100

    @api.depends('auction_date')
    def _compute_auction_date_char(self):
        for record in self:
            record.auction_date_char = record.auction_date.strftime("%d %B %Y")

    @api.model
    def create(self, vals):
        if vals.get('document_no', 'New') == 'New':
            vals['document_no'] = self.env['ir.sequence'].next_by_code('ae.auction.header') or 'New'
        return super(aeAuctionHeader, self).create(vals)
    
    def unlink(self):
        """
        Override unlink function to prevent deletion of posted document
        """
        for record in self:
            if record.status == 'posted':
                raise ValidationError("You cannot delete posted document!")
        return super(aeAuctionHeader, self).unlink()
    
    def action_posting_invle(self):
        """
        This function is used to create posting action button for inserting data to inventory ledger entries"""
        for record in self:
            if record.auction_line_ids:
                for line in record.auction_line_ids:
                    if line.quantity > 0:
                        # create inventory ledger entries
                        self.env['ae.inventory.ledger.entry'].create({
                            'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                            'line_no': line.line_no,
                            'inventory_name': line.inventory.inventory_name,
                            'document_type': "3",
                            'inventory_type': line.inventory.inventory_type,
                            'inventory_label': line.inventory.inventory_label,
                            'inventory_number': line.inventory.inventory_number,
                            'asset_number': line.inventory.inventory_asset_number,
                            'posting_date': record.posting_date,
                            'location_code': line.inventory.inventory_location_code.location_code,
                            'quantity': line.quantity * -1,
                            'unit_of_measure': line.inventory.inventory_unit_of_measure.name,
                            'document_no': record.document_no,
                            'entry_type': '17',
                        })

                        # Update quantity in inventory master
                        line.inventory.inventory_qty = line.inventory.inventory_qty - line.quantity
                        line.inventory.inventory_status = '2'
                        line.inventory.active = False
                    else:
                        raise ValidationError("Quantity must be greater than 0!")
            else:
                raise ValidationError("Item Journal Lines are required!")
            
            # change status to posted
            record.status = 'posted'

    # Section function

class aeAuctionLine(models.Model):
    _name = 'ae.auction.line'
    _description = 'Auction Report Line'

    line_no = fields.Integer(string='Line No',readonly=True,store=True, compute='_compute_line_no')
    auction_header_id = fields.Many2one('ae.auction.header', string='Auction Header', ondelete='cascade')

    document_no = fields.Char(string='Document No', related='auction_header_id.document_no')
    posting_date = fields.Datetime(string='Posting Date', related='auction_header_id.posting_date')
    lot_no = fields.Char(string='Lot No', related='auction_header_id.lot_no')
    
    inventory = fields.Many2one('ae.inventory', string='Inventory')
    inventory_label = fields.Char(string='Inventory Label', related='inventory.inventory_label')
    inventory_no = fields.Char(string='Inventory No.', related='inventory.inventory_number')
    inventory_uom = fields.Many2one('uom.uom', string='UOM', readonly=True)
    inventory_status = fields.Selection(string='Inventory Status', related='inventory.inventory_status')
    inventory_location = fields.Many2one('ae.location', string='Location', related='inventory.inventory_location_code')
    asset_no = fields.Char(string='Asset No.', related='inventory.inventory_asset_number')
    disposal_method = fields.Selection(string='Disposal Method', related='inventory.inventory_status')
    disposal_picture = fields.Binary(string='Discposal Picture')
    quantity = fields.Integer(string='Quantity')
    inventory_type = fields.Selection([
        ('1', 'Inventory'),
        ('2', 'Asset'),
        ('3', 'Attractive Items'),
        ('4', 'Stationary & Supplies'),
        ('5', 'Settling Kit')
    ], string='Inventory Type', related='inventory.inventory_type')
    
    # Section function
    @api.onchange('inventory')
    def _onchange_inventory(self):
        """
        Set inventory uom
        """
        for record in self:
            record.inventory_uom = record.inventory.inventory_unit_of_measure.id

    @api.depends('auction_header_id.auction_line_ids')
    def _compute_line_no(self):
        for record in self:
            record.line_no = 0
            for line in record.auction_header_id.auction_line_ids:
                if line.id == record.id:
                    record.line_no += 1
                    break
                else:
                    record.line_no += 1

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """
        Quantity cannot be greater than inventory quantity
        """
        if self.quantity > self.inventory.inventory_qty:
            raise ValidationError("Quantity cannot be greater than inventory quantity! Now inventory quantity is %s" % self.inventory.inventory_qty)
    # Section function
