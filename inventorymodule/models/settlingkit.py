from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class aeSettlingKitHeader(models.Model):
    _name = 'ae.settlingkit.header'
    _description = 'Settling Kit Header'
    _rec_name = 'document_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'posting_date desc'

    active = fields.Boolean(default=True)
    document_no = fields.Char(string='Document No', required=True, readonly=True, default='New')
    posting_date = fields.Datetime(string='Posting Date',default=fields.Datetime.now, required=True)
    location_name = fields.Many2one('ae.location', string='Location Name', required=True)
    settling_type = fields.Selection([
        ('1', 'Settling In'),
        ('2', 'Settling Out'),
    ], string='Settling Type', required=True, default='1')

    tenant_name = fields.Char(string='Tenant Name', size=100)
    tenant_address = fields.Text(string='Tenant Address', size=100)
    delivery_date = fields.Date(string='Delivery Date')
    returned_date = fields.Date(string='Returned Date', store=True)
    notes = fields.Char(string='Notes')

    total_quantity_returned = fields.Integer(string='Total Quantity Returned', compute='_compute_total_quantity_returned', store=True)
    total_quantity_shipped = fields.Integer(string='Total Quantity Shipped', compute='_compute_total_quantity_shipped', store=True)

    status = fields.Selection([
        ('open', 'Open'),
        ('shipped', 'Delivered'),
        ('returned', 'Returned'),
    ], string='Status', default='open')
   
    settling_kit_line_ids = fields.One2many('ae.settlingkit.line', 'settling_kit_header_id', string='Settling Kit Lines')
    agency_name = fields.Many2one('ae.master.agency', string='Agency Name')

    delivery_date_char = fields.Char(string='Delivery Date', compute='_compute_delivery_date_char', store=True)
    returned_date_char = fields.Char(string='Returned Date', compute='_compute_returned_date_char', store=True)
    posting_date_only = fields.Date(string='Posting Date', compute='_compute_posting_date_only', store=True)

    # 19 04 2024
    is_non_dfat = fields.Boolean(string='Non DFAT', default=False, help='This field will be automatically checked if the agency is non DFAT', readonly=True, store=True)

    # Section function

    @api.onchange('agency_name')
    def _onchange_agency_name(self):
        for record in self:
            if record.agency_name:
                record.is_non_dfat = record.agency_name.is_non_dfat

    @api.depends('posting_date')
    def _compute_posting_date_only(self):
        for record in self:
            record.posting_date_only = record.posting_date.date()

    # Hide Filter dropdown for Inventory Type
    def get_fields_to_ignore_in_search(self):
        return ['delivery_date_char', 'returned_date_char']
    
    def fields_get(self, allfields=None, attributes=None):
        res = super(aeSettlingKitHeader, self).fields_get(allfields=allfields, attributes=attributes)
        for field in self.get_fields_to_ignore_in_search():
            if res.get(field):
                res.get(field)['searchable'] = False
        return res

    def action_print_setkit_report(self):
        return self.env.ref('inventorymodule.action_report_settlingkitsinout').report_action(self)

    @api.depends('delivery_date')
    def _compute_delivery_date_char(self):
        for record in self:
            if record.delivery_date:
                record.delivery_date_char = record.delivery_date.strftime('%d %B %Y')

    @api.depends('returned_date')
    def _compute_returned_date_char(self):
        for record in self:
            if record.returned_date:
                record.returned_date_char = record.returned_date.strftime('%d %B %Y')

    # Return date is 7 days after delivery date
    @api.onchange('delivery_date')
    def _onchange_delivery_date(self):
        for record in self:
            if record.delivery_date:
                record.returned_date = record.delivery_date + timedelta(days=30)
    
    @api.model
    def create(self, vals):
        if vals.get('document_no', 'New') == 'New':
            vals['document_no'] = self.env['ir.sequence'].next_by_code('ae.settlingkit.header') or 'New'
        return super(aeSettlingKitHeader, self).create(vals)

    def unlink(self):
        """
        This function is used to delete record
        """
        for record in self:
            if record.status != 'open':
                raise ValidationError("You cannot delete record that has been shipped or returned")
        return super(aeSettlingKitHeader, self).unlink()
    
    # Button Posting
    def action_posting_shipped(self):
        """
        This function is used to create posting action button for inserting data to inventory ledger entries"""
        for record in self:
            if record.settling_kit_line_ids:
                for line in record.settling_kit_line_ids:
                    if line.quantity > 0:
                        # create inventory ledger entries
                        self.env['ae.inventory.ledger.entry'].create({
                            'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                            'document_no': record.document_no,
                            'line_no': line.line_no,
                            'inventory_id': line.inventory.id,
                            'inventory_name': line.inventory.inventory_name,
                            'document_type': '2',
                            'inventory_type': line.inventory.inventory_type,
                            'entry_type': "12",
                            'inventory_label': line.inventory.inventory_label,
                            'inventory_number': line.inventory.inventory_number,
                            'posting_date': record.posting_date,
                            'delivery_date': record.delivery_date,
                            'from_location_code': line.inventory.inventory_location_code.id,
                            # 'to_location_code': record.location_name.id,
                            'quantity': line.quantity * -1,
                            'unit_of_measure': line.inventory.inventory_unit_of_measure.name,
                            'updated_by': self.env.user.id,
                            'updated_date': fields.Date.today(),
                            'remarks': line.notes,
                        })

                        self.env['ae.inventory.ledger.entry'].create({
                            'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                            'document_no': record.document_no,
                            'line_no': line.line_no,
                            'inventory_id': line.inventory.id,
                            'inventory_name': line.inventory.inventory_name,
                            'document_type': '2',
                            'inventory_type': line.inventory.inventory_type,
                            'entry_type': "12",
                            'inventory_label': line.inventory.inventory_label,
                            'inventory_number': line.inventory.inventory_number,
                            'posting_date': record.posting_date,
                            'delivery_date': record.delivery_date,
                            # 'from_location_code': record.location_name.id,
                            'to_location_code': record.location_name.id,
                            'quantity': line.quantity,
                            'unit_of_measure': line.inventory.inventory_unit_of_measure.name,
                            'updated_by': self.env.user.id,
                            'updated_date': fields.Date.today(),
                            'remarks': line.notes,
                        })

                        # update inventory master
                        line.inventory.inventory_qty = line.inventory.inventory_qty - line.quantity
                    else:
                        raise ValidationError("Quantity must be greater than 0!")
            else:
                raise ValidationError("Item Journal Lines are required!")
            
            # change status to posted
            record.status = 'shipped'


            
    # Button Return
    def action_posting_returned(self):
        """
        This function is used to create posting action button for inserting data to inventory ledger entries"""
        for record in self:
            if record.settling_kit_line_ids and record.status == 'shipped':
                for line in record.settling_kit_line_ids:
                    if line.return_quantity > 0:
                        self.env['ae.inventory.ledger.entry'].create({
                            'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                            'document_no': record.document_no,
                            'line_no': line.line_no,
                            'returned_date': record.returned_date,
                            'inventory_id': line.inventory.id,
                            'inventory_name': line.inventory.inventory_name,
                            'document_type': '2',
                            'inventory_type': line.inventory.inventory_type,
                            'entry_type': "16",
                            'inventory_label': line.inventory.inventory_label,
                            'inventory_number': line.inventory.inventory_number,
                            'posting_date': record.posting_date,
                            'delivery_date': record.delivery_date,
                            'from_location_code': record.location_name.id,
                            # 'to_location_code': record.location_name.id,
                            # 'quantity': line.quantity,
                            'unit_of_measure': line.inventory.inventory_unit_of_measure.name,
                            'updated_by': self.env.user.id,
                            'updated_date': fields.Date.today(),
                            'remarks': line.notes,
                            'return_quantity': -1*line.return_quantity,
                        })

                        self.env['ae.inventory.ledger.entry'].create({
                            'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                            'document_no': record.document_no,
                            'line_no': line.line_no,
                            'inventory_id': line.inventory.id,
                            'inventory_name': line.inventory.inventory_name,
                            'document_type': '2',
                            'inventory_type': line.inventory.inventory_type,
                            'entry_type': "16",
                            'returned_date': record.returned_date,
                            'inventory_label': line.inventory.inventory_label,
                            'inventory_number': line.inventory.inventory_number,
                            'posting_date': record.posting_date,
                            'delivery_date': record.delivery_date,
                            # 'from_location_code': record.location_name.id,
                            'to_location_code': line.inventory.inventory_location_code.id,
                            # 'quantity': line.quantity * -1,
                            'unit_of_measure': line.inventory.inventory_unit_of_measure.name,
                            'updated_by': self.env.user.id,
                            'updated_date': fields.Date.today(),
                            'remarks': line.notes,
                            'return_quantity': line.return_quantity,
                        })

                        #Update Inventory Master
                        line.inventory.inventory_qty = line.inventory.inventory_qty + line.return_quantity
                    else:
                        raise ValidationError("Quantity must be greater than 0!")
            else:
                raise ValidationError("Item Journal Lines are required!")
            
            
            # change status to posted
            record.status = 'returned'

            if record.total_quantity_returned != record.total_quantity_shipped:
                self.env['ae.inventory.ledger.entry'].create({
                    'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                    'document_no': record.document_no,
                    'line_no': line.line_no,
                    'inventory_id': line.inventory.id,
                    'inventory_name': line.inventory.inventory_name,
                    'document_type': '2',
                    'inventory_type': line.inventory.inventory_type,
                    'entry_type': "13",
                    'inventory_label': line.inventory.inventory_label,
                    'inventory_number': line.inventory.inventory_number,
                    'posting_date': record.posting_date,
                    'delivery_date': record.delivery_date,
                    'from_location_code': record.location_name.id,
                    # 'to_location_code': line.inventory.inventory_location_code.id,
                    'quantity': (record.total_quantity_shipped - record.total_quantity_returned)*-1,
                    'unit_of_measure': line.inventory.inventory_unit_of_measure.name,
                    'updated_by': self.env.user.id,
                    'updated_date': fields.Date.today(),
                    'remarks': line.notes,
                    'returned_date': record.returned_date,
                })

    @api.depends('settling_kit_line_ids.quantity')
    def _compute_total_quantity_shipped(self):
        for record in self:
            total_quantity_shipped = 0
            for line in record.settling_kit_line_ids:
                total_quantity_shipped += line.quantity
            record.total_quantity_shipped = total_quantity_shipped

    @api.depends('settling_kit_line_ids.return_quantity')
    def _compute_total_quantity_returned(self):
        for record in self:
            total_quantity_returned = 0
            for line in record.settling_kit_line_ids:
                total_quantity_returned += line.return_quantity
            record.total_quantity_returned = total_quantity_returned    

    # Section function

class aeSettlingKitLine(models.Model):
    _name = 'ae.settlingkit.line'
    _description = 'Settling Kit Line'

    line_no = fields.Integer(string='Line No',readonly=True,store=True, compute='_compute_line_no')
    settling_kit_header_id = fields.Many2one('ae.settlingkit.header', string='Settling Kit Header', ondelete='cascade')

    inventory_setkit_group = fields.Many2one('ae.settling.master.group', string='Inventory Setkit Group')

    document_no = fields.Char(string='Document No', related='settling_kit_header_id.document_no')
    # posting_date = fields.Date(string='Posting Date', related='settling_kit_header_id.posting_date')
    posting_date = fields.Datetime(string='Posting Date', related='settling_kit_header_id.posting_date')
    inventory = fields.Many2one('ae.inventory', string='Inventory', required=True)
    inventory_label = fields.Char(string='Inventory Label')
    inventory_no = fields.Char(string='Inventory No.', related='inventory.inventory_number')
    to_location_line = fields.Many2one('ae.location', string='To Location', related='settling_kit_header_id.location_name', readonly=True)
    from_location_line = fields.Many2one('ae.location', string='From Location', related='inventory.inventory_location_code', readonly=True)
    unit_of_measure = fields.Many2one('uom.uom', string='Unit of Measure', store=True)
    quantity = fields.Integer(string='Quantity', required=True)
    return_quantity = fields.Integer(string='Return Quantity')
    notes = fields.Char(string='Notes')
    status = fields.Selection([
        ('open', 'Open'),
        ('shipped', 'Delivered'),
        ('returned', 'Returned'),
    ], string='Status', related='settling_kit_header_id.status')

    # If inventory label is not empty, will automatically detect inventory
    @api.onchange('inventory_label')
    def _onchange_inventory_label(self):
        for record in self:
            if record.inventory_label:
                record.inventory = self.env['ae.inventory'].search([('inventory_label', '=', record.inventory_label)])

    @api.onchange('inventory')
    def _onchange_inventory(self):
        for record in self:
            record.unit_of_measure = record.inventory.inventory_unit_of_measure.id
            record.inventory_label = record.inventory.inventory_label
            record.inventory_setkit_group = record.inventory.inventory_settling_master_group.id

    @api.depends('settling_kit_header_id.settling_kit_line_ids')
    def _compute_line_no(self):
        for record in self:
            record.line_no = 0
            for line in record.settling_kit_header_id.settling_kit_line_ids:
                if line.id == record.id:
                    record.line_no += 1
                    break
                else:
                    record.line_no += 1

    @api.onchange('quantity')
    def _onchange_quantity(self):
        for record in self:
            if record.settling_kit_header_id.settling_type in ('1', '2'):
                if record.quantity > record.inventory.inventory_qty:
                    raise ValidationError("Quantity must be less than or equal to the available quantity in the inventory! Now available: %s" % record.inventory.inventory_qty)
                
    @api.onchange('return_quantity')
    def _onchange_return_quantity(self):
        for record in self:
            if record.settling_kit_header_id.settling_type in ('1', '2'):
                if record.return_quantity > record.quantity:
                    raise ValidationError("Return Quantity must be less than or equal to the shipped quantity! Now shipped: %s" % record.quantity)
    # Section function