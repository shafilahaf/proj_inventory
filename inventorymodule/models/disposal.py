from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta

class aeDisposalHeader(models.Model):
    _name = 'ae.disposal.header'
    _description = 'Disposal Header'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'posting_date desc'
    _rec_name = 'document_no'

    active = fields.Boolean(default=True)
    document_no = fields.Char(string='Document No', required=True, readonly=True, default='New')
    posting_date = fields.Datetime(string='Posting Date',default=fields.Datetime.now, required=True)
    posting_date_char = fields.Char(string='Posting Date Char', compute='_compute_posting_date_char', store=True)
    disposal_method = fields.Selection('get_disposal_method', string='Disposal Method', required=True)
    disposal_method_setkit = fields.Selection([
        ('1', 'Write-Off'),
        ('3', 'Destroyed'),
    ], string='Disposal Method', default='1', store=True)
    status = fields.Selection([
        ('open', 'Open'),
        ('released', 'Released'),
        ('posted', 'Posted'),
    ], string='Status', default='open',store=True)
    notes = fields.Text(string='Notes')
    location_code = fields.Many2one('ae.location', string='Auction Location')
    am3_disposal_form = fields.Binary(string='AM3 Disposal Form')
    line_ids = fields.One2many('ae.disposal.line', 'header_id', string='Disposal Lines')
    inventory_type = fields.Selection([
        ('2', 'Asset'), ('3', 'Settling Kit'), ('1', 'Inventory')
    ], string='Type', store=True)

    inventory_type_asset = fields.Selection([
        ('2', 'Asset'), ('1', 'Inventory')], string='Type')
    
    inventory_type_setkit = fields.Selection([
        ('3', 'Settling Kit')], string='Type', default='3', readonly=True)
    
    isDisposalInventory = fields.Boolean(string='Is Disposal Inventory', default=True)
    isDisposalSetkit = fields.Boolean(string='Is Disposal Settling Kit', default=True)
    
    # Section function
    @api.model
    def get_disposal_method(self):
        return [
            ('1', 'Write-Off'),
            ('2', 'Auction'),
            ('3', 'Destroyed'),
        ]
    
    @api.onchange('disposal_method_setkit')
    def _onchange_disposal_method_setkit(self):
        if self.disposal_method_setkit == '1':
            self.disposal_method = '1'
        elif self.disposal_method_setkit == '3':
            self.disposal_method = '3'

    @api.onchange('line_ids')
    def _onchange_line_ids(self):
        # Cannot duplicate inventory
        for record in self:
            if record.line_ids:
                inventory_list = []
                for line in record.line_ids:
                    if line.inventory.inventory_label in inventory_list:
                        raise ValidationError("Inventory with label %s is entered more than once!" % line.inventory.inventory_label)
                    else:
                        inventory_list.append(line.inventory.inventory_label)

    @api.depends('posting_date')
    def _compute_posting_date_char(self):
        for record in self:
            if record.posting_date:
                adjusted_date = record.posting_date + timedelta(hours=7)
                record.posting_date_char = adjusted_date.strftime("%d %B %Y %H:%M:%S")

    @api.model
    def create(self, vals):
        # if vals.get('document_no', 'New') == 'New':
        #     vals['document_no'] = self.env['ir.sequence'].next_by_code('ae.disposal.header') or 'New'

        if vals['inventory_type'] == '1' or vals['inventory_type'] == '2':
            vals['document_no'] = self.env['ir.sequence'].next_by_code('ae.disposal.asset') or 'New'
        elif vals['inventory_type'] == '3':
            vals['document_no'] = self.env['ir.sequence'].next_by_code('ae.disposal.setkit') or 'New'

        return super(aeDisposalHeader, self).create(vals)
    
    def unlink(self):
        """
        This function is used to prevent delete record if status is not open
        """
        for record in self:
            if record.status != 'open':
                raise UserError(_('You can not delete record if status is not open'))
        return super(aeDisposalHeader, self).unlink()

    @api.onchange('inventory_type_asset')
    def _onchange_inventory_type_asset(self):
        """
        This function is used to change inventory type based on inventory type asset"""
        if self.inventory_type_asset == '1':
            self.inventory_type = '1'
        elif self.inventory_type_asset == '2':
            self.inventory_type = '2'

    @api.onchange('inventory_type_setkit')
    def _onchange_inventory_type_setkit(self):
        """
        This function is used to change inventory type based on inventory type settling kit"""
        if self.inventory_type_setkit == '3':
            self.inventory_type = '3'

    def action_release(self):
        # self.status = 'released'
        if not self.line_ids:
            raise UserError(_('You can not release document if disposal line is empty'))
        else:
            self.status = 'released'

    def action_reset_draft(self):
        self.status = 'open'

    def action_posting_invle(self):
        for record in self:
            if record.line_ids:
                for line in record.line_ids:
                    if line.quantity > 0:
                        # create inventory ledger entries
                        entry_type_map = {
                            '1': '6',  # Write-Off
                            '2': '5',  # Auction
                            '3': '7',  # Destroyed
                        }
                        entry_type = entry_type_map.get(record.disposal_method)
                        if entry_type:
                            if record.disposal_method == '2':
                
                                self.env['ae.inventory.ledger.entry'].create({
                                    'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                                    'line_no': line.line_no,
                                    'inventory_id': line.inventory.id,
                                    'inventory_name': line.inventory.inventory_name,
                                    'document_type': "5",
                                    'entry_type':  entry_type,
                                    'inventory_type': line.inventory.inventory_type,
                                    'asset_number': line.inventory.inventory_asset_number,
                                    'posting_date': record.posting_date,
                                    'from_location_code': line.inventory.inventory_location_code.id,
                                    'to_location_code': record.location_code.id,
                                    'location_code': line.inventory.inventory_location_code.location_name,
                                    'quantity': line.quantity * -1,
                                    'document_no': record.document_no,
                                    'remarks': line.remarks,
                                    'location_code': line.inventory_location_code.location_code, 
                                    'room_code': line.inventory_room_code.room_code,
                                    'sub_room_code': line.inventory_sub_room_code.sub_room_code, 
                                })

                                self.env['ae.inventory.ledger.entry'].create({
                                    'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                                    'line_no': line.line_no,
                                    'inventory_id': line.inventory.id,
                                    'inventory_name': line.inventory.inventory_name,
                                    'document_type': "5",
                                    'entry_type':  entry_type,
                                    'inventory_type': line.inventory.inventory_type,
                                    'asset_number': line.inventory.inventory_asset_number,
                                    'posting_date': record.posting_date,
                                    'from_location_code': record.location_code.id,
                                    'to_location_code': line.inventory.inventory_location_code.id,
                                    'location_code': line.inventory.inventory_location_code.location_name,
                                    'quantity': line.quantity,
                                    'document_no': record.document_no,
                                    'remarks': line.remarks,
                                    'location_code': line.inventory_location_code.location_code, 
                                    'room_code': line.inventory_room_code.room_code,
                                    'sub_room_code': line.inventory_sub_room_code.sub_room_code, 
                                    
                                })

                            else:
                                self.env['ae.inventory.ledger.entry'].create({
                                    'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                                    'line_no': line.line_no,
                                    'inventory_id': line.inventory.id,
                                    'inventory_name': line.inventory.inventory_name,
                                    'document_type': "5",
                                    'entry_type':  entry_type,
                                    'inventory_type': line.inventory.inventory_type,
                                    'asset_number': line.inventory.inventory_asset_number,
                                    'posting_date': record.posting_date,
                                    'from_location_code': line.inventory.inventory_location_code.id,
                                    'to_location_code': record.location_code.id,
                                    'location_code': line.inventory.inventory_location_code.location_name,
                                    'quantity': -1*line.quantity,
                                    'document_no': record.document_no,
                                    'remarks': line.remarks,
                                    'location_code': line.inventory_location_code.location_code, 
                                    'room_code': line.inventory_room_code.room_code,
                                    'sub_room_code': line.inventory_sub_room_code.sub_room_code, 
                                })

                                # Update inventory master quantity
                                line.inventory.inventory_qty = line.inventory.inventory_qty - line.quantity
                                # Update inventory status to disposed
                                line.inventory.inventory_status = '2'
                                # line.inventory.active = False
                                # If inventory type is inventory or asset, active is false
                                if line.inventory.inventory_type in ['1', '2']:
                                    line.inventory.active = False
                                
                        else:
                            raise ValidationError("Invalid disposal method!")
                    else:
                        raise ValidationError("Quantity must be greater than zero!")
            else:
                raise ValidationError("Item Journal Lines are required!")

            # change status to posted
            record.status = 'posted'

            if record.disposal_method == '2':
                for line in record.line_ids:
                    line.inventory.inventory_location_code = record.location_code.id

    
    # Report id = action_report_inventorydisposal
    def action_print_inventory_asset_disposal(self):
        return self.env.ref('inventorymodule.action_report_inventorydisposal').report_action(self)
    
    # Report id = action_report_inventorydisposalsetkit
    def action_print_inventory_setkit_disposal(self):
        return self.env.ref('inventorymodule.action_report_inventorydisposalsetkit').report_action(self)
    
    # Hide Filter dropdown for Inventory Type
    def get_fields_to_ignore_in_search(self):
        return ['disposal_method_setkit', 'inventory_type_setkit', 'inventory_type_asset']
    
    def fields_get(self, allfields=None, attributes=None):
        res = super(aeDisposalHeader, self).fields_get(allfields=allfields, attributes=attributes)
        for field in self.get_fields_to_ignore_in_search():
            if res.get(field):
                res.get(field)['searchable'] = False
        return res
    
    # Section function

class aeDisposalLine(models.Model):
    _name = 'ae.disposal.line'
    _description = 'Disposal Line'

    header_id = fields.Many2one('ae.disposal.header', string='Header ID', ondelete='cascade')
    line_no = fields.Integer(string='Line No',readonly=True,store=True, compute='_compute_line_no')
    inventory = fields.Many2one('ae.inventory', string='Inventory Name', required=True)
    inventory_label = fields.Char(string='Inventory Label', store="True")
    inventory_name = fields.Char(string='Inventory Name', related='inventory.inventory_name')
    inventory_type = inventory_type = fields.Selection([
        ('1', 'Inventory'),
        ('2', 'Asset'),
        ('3', 'Attractive Items'),
        ('4', 'Stationary & Supplies'),
        ('5', 'Settling Kit'),
    ], string='Type', related='inventory.inventory_type')
    inventory_type_header = fields.Selection([
        ('1', 'Asset'), ('3', 'Settling Kit'), ('2', 'Inventory')
    ], string='Type', related='header_id.inventory_type', store=True)
    inventory_asset_number = fields.Char(string='Asset No.', related='inventory.inventory_asset_number')
    disposal_picture = fields.Binary(string='Disposal Picture', store=True)
    disposal_picture_data = fields.Char(string='Disposal Picture Data', compute='_compute_disposal_picture_data', store=True)
    # inventory_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True, readonly=True)
    inventory_uom = fields.Char(string='Unit of Measure', readonly=True)
    inventory_location_code = fields.Many2one('ae.location', string='Location Code', required=True, readonly=True)
    # inventory_room_code = fields.Many2one('ae.master.room', string='Room Code', domain="[('id', 'in', available_rooms)]", required=True, readonly=True)
    # inventory_sub_room_code = fields.Many2one('ae.master.sub.room', string='Sub Room Code', domain="[('id', 'in', available_sub_rooms)]", required=True, readonly=True)
    inventory_room_code = fields.Many2one('ae.master.room', string='Room Code', readonly=True)
    inventory_sub_room_code = fields.Many2one('ae.master.sub.room', string='Sub Room Code', readonly=True)
    available_rooms = fields.Many2many('ae.master.room', compute='_compute_available_rooms')
    available_sub_rooms = fields.Many2many('ae.master.sub.room', compute='_compute_available_sub_rooms')
    condition = fields.Selection([
        ('1', 'Good'),
        ('2', 'Poor'),
    ], string='Condition', required=True)
    remarks = fields.Char(string='Remarks')
    disposal_method = fields.Selection([
        ('1', 'Write-Off'),
        ('2', 'Auction'),
        ('3', 'Destroyed'),
    ], string='Disposal Method', related='header_id.disposal_method')
    quantity = fields.Integer(string='Quantity', required=True, default=1)
    
    # Section function
    @api.onchange('quantity')
    def _onchange_quantity(self):
        """
        This function is to check quantity cannot greater than inventory quantity
        """
        if self.inventory:
            if self.quantity > self.inventory.inventory_qty:
                raise ValidationError("Quantity cannot greater than inventory quantity! Now inventory quantity is %s" % self.inventory.inventory_qty)

    @api.depends('header_id.line_ids')
    def _compute_line_no(self):
        for record in self:
            record.line_no = 0
            for line in record.header_id.line_ids:
                if line.id == record.id:
                    record.line_no += 1
                    break
                else:
                    record.line_no += 1

    @api.depends('disposal_picture')
    def _compute_disposal_picture_data(self):
        for record in self:
            record.disposal_picture_data = record.disposal_picture

    @api.depends('inventory_location_code')
    def _compute_available_rooms(self):
        """
        Get available rooms from location_details_id."""
        for record in self:
            record.available_rooms = record.inventory_location_code.location_details_id.mapped('room_code')

    @api.depends('inventory_room_code')
    def _compute_available_sub_rooms(self):
        """
        Get available sub rooms from location_details_id."""
        # for record in self:
        #     record.available_sub_rooms = record.inventory_room_code.location_details_ids.mapped('sub_room_code')
        for record in self:
            record.available_sub_rooms = record.inventory_location_code.location_details_id.filtered(lambda r: r.room_code.id == record.inventory_room_code.id).mapped('sub_room_code')

    @api.onchange('inventory')
    def _onchange_inventory(self):
        """
        This function is used to change inventory type based on inventory type asset"""
        if self.inventory:
            self.inventory_location_code = self.inventory.inventory_location_code.id if self.inventory.inventory_location_code else False
            self.inventory_room_code = self.inventory.inventory_room_code.id if self.inventory.inventory_room_code else False
            self.inventory_sub_room_code = self.inventory.inventory_sub_room_code.id if self.inventory.inventory_sub_room_code else False
            self.inventory_uom = self.inventory.inventory_unit_of_measure.name if self.inventory.inventory_unit_of_measure else False
            self.inventory_label = self.inventory.inventory_label if self.inventory.inventory_label else False

    @api.onchange('inventory_label')
    def _onchange_inventory_label(self):
        for record in self:
            if record.inventory_label:
                inventory = self.env['ae.inventory'].search([('inventory_label', '=', record.inventory_label)])
                if inventory:
                    record.inventory = inventory.id
                else:
                    raise ValidationError("Inventory with label %s is not found in the system!" % record.inventory_label)
    # Section function