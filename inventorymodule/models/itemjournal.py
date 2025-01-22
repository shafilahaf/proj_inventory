from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import math

class aeItemJournalHeader(models.Model):
    _name = 'ae.itemjournal.header'
    _description = 'Item Journal Header'
    _rec_name = 'reference_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'posting_date desc'

    receipt_by = fields.Char(string='Receipt By')
    active = fields.Boolean(default=True)
    posting_date = fields.Datetime(string='Posting Date', default=fields.Datetime.now, required=True)
    entry_type = fields.Selection([
        ('1', 'Stock In'), #+
        ('2', 'Stock Out'),
        ('3', 'Consumption'),
        ('4', 'Purchase'),#+
        ('5', 'Sales'),
        ('6', 'Sales Return'),#+
    ], string='Entry Type')
    item_type = fields.Selection([
        ('1', 'Attractive Items'),
        ('2', 'Stationery & Supplies'),
        ('3', 'Settling Kit'),
    ], string='Item Type')

    item_type_attractive = fields.Selection([('1', 'Attractive Items')], string='Item Type', default='1')
    entry_type_attractive = fields.Selection([('1', 'Stock In'), ('2', 'Stock Out')], string='Entry Type')
    entry_type_attractive_consumption = fields.Selection([('3', 'Consumption')], string='Entry Type', default='3', readonly=True)

    item_type_purchase = fields.Selection([('2', 'Stationery & Supplies')], string='Item Type', default='2')
    entry_type_purchase = fields.Selection([('4', 'Purchase')], string='Entry Type', default='4')

    item_type_sales = fields.Selection([('2', 'Stationery & Supplies')], string='Item Type', default='2')
    entry_type_sales = fields.Selection([('5', 'Sales')], string='Entry Type', default='5')

    item_type_stasup = fields.Selection([('2', 'Stationery & Supplies')], string='Item Type', default='2')
    entry_type_stasup = fields.Selection([('1', 'Stock In'), ('2', 'Stock Out')], string='Entry Type')

    item_type_setkit = fields.Selection([('3', 'Settling Kit')], string='Item Type', default='3')
    entry_type_setkit = fields.Selection([('1', 'Stock In'), ('2', 'Stock Out')], string='Entry Type')

    item_type_salesreturn = fields.Selection([('2', 'Stationery & Supplies')], string='Item Type', default='2')
    entry_type_salesreturn = fields.Selection([('6', 'Sales Return')], string='Entry Type', default='6', readonly=True)

    state = fields.Selection([('open', 'Open'), ('posted', 'Posted')], string='Status', default='open', required=True)

    vendor_name = fields.Many2one('ae.master.vendor', string='Vendor Name', store=True)
    customer_name = fields.Many2one('ae.master.customer', string='Customer Name', store=True)
    pic = fields.Char(string='PIC')

    reference_no = fields.Char(string='Document No.', readonly=True, required=True, default='New', store=True)

    total_amount = fields.Integer(string='Total Amount', readonly=True, compute='_compute_total_amount')

    isStationeryIssued = fields.Boolean(string='Stationery Issued')
    stationery_document_no = fields.Char(string='Stationery Issued Document')


    item_journal_line_ids = fields.One2many('ae.itemjournal.line', 'item_journal_header_id', string='Item Journal Lines')

    subtotal = fields.Integer(string='Subtotal', compute='_compute_subtotal', readonly=True, store=True)
    posting_date_only = fields.Date(string='Posting Date', compute='_compute_posting_date_only', store=True)

    # Section function

    @api.depends('posting_date')
    def _compute_posting_date_only(self):
        for record in self:
            record.posting_date_only = record.posting_date.date()

    def get_fields_to_ignore_in_search(self):
        return ['entry_type_attractive', 'entry_type_purchase', 'entry_type_sales', 'entry_type_stasup', 'entry_type_salesreturn', 'entry_type_setkit', 'item_type_attractive', 'entry_type_attractive_consumption', 'item_type_purchase', 
                'item_type_sales', 'item_type_stasup', 'item_type_setkit', 'item_type_salesreturn']
    
    def fields_get(self, allfields=None, attributes=None):
        res = super(aeItemJournalHeader, self).fields_get(allfields=allfields, attributes=attributes)
        for field in self.get_fields_to_ignore_in_search():
            if res.get(field):
                res.get(field)['searchable'] = False
        return res

    @api.depends('item_journal_line_ids')
    def _compute_subtotal(self):
        for rec in self:
            subtotal = 0
            for line in rec.item_journal_line_ids:
                subtotal += line.total
            rec.subtotal = subtotal

    @api.depends('item_journal_line_ids')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.item_journal_line_ids:
                total_amount += line.total_source_price
            rec.total_amount = total_amount

    @api.model
    def create(self, vals):
        """
        This function is used to override create method.
        """
        # if vals.get('reference_no', 'New') == 'New':
        #     vals['reference_no'] = self.env['ir.sequence'].next_by_code('ae.itemjournal.header.default') or 'New'
        item_type = vals.get('item_type')
        entry_type = vals.get('entry_type')

        sequence_code = 'ae.itemjournal.header.default'  # Default sequence code

        if entry_type == '1' or entry_type == '2':  # Stock In
            if item_type == '1':  # Attractive Items
                sequence_code = 'ae.itemjournal.header.attractive.stock_in'
            elif item_type == '2':  # Stationery & Supplies
                sequence_code = 'ae.itemjournal.header.stassup.stock_in'
            elif item_type == '3':  # Settling Kit
                sequence_code = 'ae.itemjournal.header.setkit.stock_in'
        # elif entry_type == '2':  # Stock Out
        #     if item_type == '1':  # Attractive Items
        #         sequence_code = 'ae.itemjournal.header.attractive.stock_out'
        #     elif item_type == '2':  # Stationery & Supplies
        #         sequence_code = 'ae.itemjournal.header.stassup.stock_out'
        #     elif item_type == '3':  # Settling Kit
        #         sequence_code = 'ae.itemjournal.header.setkit.stock_out'
        elif entry_type == '3':  # Consumption
            if item_type == '1':
                sequence_code = 'ae.itemjournal.header.attractive.consumption'
            elif item_type == '2':
                sequence_code = 'ae.itemjournal.header.stassup.consumption'
            elif item_type == '3':
                sequence_code = 'ae.itemjournal.header.setkit.consumption'
        elif entry_type == '4':  # Purchase
            sequence_code = 'ae.itemjournal.header.purchase'
        elif entry_type == '5':  # Sales
            sequence_code = 'ae.itemjournal.header.sales'
        elif entry_type == '6':  # Sales Return
            if item_type == '2':
                sequence_code = 'ae.itemjournal.header.stassup.sales_return'

        # Generate the document no based on the selected sequence
        vals['reference_no'] = self.env['ir.sequence'].next_by_code(sequence_code) or 'New'


        if vals.get('item_journal_line_ids'):
            for line in vals.get('item_journal_line_ids'):
                line[2]['reference_no'] = vals.get('reference_no')
            
        return super(aeItemJournalHeader, self).create(vals)


    def unlink(self):
        """
        This function is used to delete a record.
        """
        for rec in self:
            if rec.state == 'posted':
                raise UserError('You cannot delete a posted record.')
        return super(aeItemJournalHeader, self).unlink()

    @api.onchange('item_type_attractive')
    def _onchange_item_type_attractive(self):
        """
        This function is used to change item type based on item type attractive"""
        if self.item_type_attractive == '1':
            self.item_type = '1'

    @api.onchange('entry_type_attractive_consumption')
    def _onchange_entry_type_attractive_consumption(self):
        """
        This function is used to change entry type based on entry type attractive"""
        if self.entry_type_attractive_consumption == '3':
            self.entry_type = '3'

    @api.onchange('entry_type_salesreturn')
    def _onchange_entry_type_salesreturn(self):
        """
        This function is used to change entry type based on entry type attractive"""
        if self.entry_type_salesreturn == '6':
            self.entry_type = '6'

    @api.onchange('item_type_salesreturn')
    def _onchange_item_type_salesreturn(self):
        """
        This function is used to change item type based on item type attractive"""
        if self.item_type_salesreturn == '2':
            self.item_type = '2'

    @api.onchange('entry_type_attractive')
    def _onchange_entry_type_attractive(self):
        """
        This function is used to change entry type based on entry type attractive"""
        if self.entry_type_attractive == '1':
            self.entry_type = '1'
        elif self.entry_type_attractive == '2':
            self.entry_type = '2'
        # elif self.entry_type_attractive == '3':
        #     self.entry_type = '3'

    @api.onchange('item_type_purchase')
    def _onchange_item_type_purchase(self):
        """
        This function is used to change item type based on item type purchase"""
        if self.item_type_purchase == '2':
            self.item_type = '2'

    @api.onchange('entry_type_purchase')
    def _onchange_entry_type_purchase(self):
        """
        This function is used to change entry type based on entry type purchase"""
        if self.entry_type_purchase == '4':
            self.entry_type = '4'

    @api.onchange('item_type_sales')
    def _onchange_item_type_sales(self):
        """
        This function is used to change item type based on item type sales"""
        if self.item_type_sales == '2':
            self.item_type = '2'

    @api.onchange('entry_type_sales')
    def _onchange_entry_type_sales(self):
        """
        This function is used to change entry type based on entry type sales"""
        if self.entry_type_sales == '5':
            self.entry_type = '5'

    @api.onchange('item_type_stasup')
    def _onchange_item_type_stasup(self):
        """
        This function is used to change item type based on item type stasup"""
        if self.item_type_stasup == '2':
            self.item_type = '2'

    @api.onchange('entry_type_stasup')
    def _onchange_entry_type_stasup(self):
        """
        This function is used to change entry type based on entry type stasup"""
        if self.entry_type_stasup == '1':
            self.entry_type = '1'
        elif self.entry_type_stasup == '2':
            self.entry_type = '2'
        elif self.entry_type_stasup == '6':
            self.entry_type = '6'

    @api.onchange('item_type_setkit')
    def _onchange_item_type_setkit(self):
        """
        This function is used to change item type based on item type setkit"""
        if self.item_type_setkit == '3':
            self.item_type = '3'

    @api.onchange('entry_type_setkit')
    def _onchange_entry_type_setkit(self):
        """
        This function is used to change entry type based on entry type setkit"""
        if self.entry_type_setkit == '1':
            self.entry_type = '1'
        elif self.entry_type_setkit == '2':
            self.entry_type = '2'

    def _get_matching_inventory_entry_type(self, entry_type):
        """
        Map the entry types between itemjournal and inventory ledger entry models.
        """
        entry_type_mapping = {
            '1': '2',  # Stock In # +
            '2': '3',  # Stock Out
            '3': '8',  # Consumption
            '4': '9',  # Purchase # +
            '5': '10',  # Sales
            '6': '11',  # Sales Return # +
        }

        return entry_type_mapping.get(entry_type, False)
    
    def action_posting_invle(self):
        """
        This function is used to create posting action button for inserting data to inventory ledger entries.
        """
        for record in self:
            if record.active == False:
                raise ValidationError("This document can not be posted because it is in Archive state!")
            else:
                if record.item_journal_line_ids:
                    for line in record.item_journal_line_ids:
                        if line.quantity > 0:
                            # Get the matching inventory entry type
                            inventory_entry_type = self._get_matching_inventory_entry_type(record.entry_type)

                            qty = 0
                            if line.quantity > 0:
                                if record.entry_type == '1' or record.entry_type == '4':
                                    qty = line.quantity * line.unit_of_measure.ratio
                                elif record.entry_type == '5':
                                    qty = line.quantity * line.unit_of_measure.ratio * -1
                                elif record.entry_type == '6':
                                    qty = line.quantity_returned * line.unit_of_measure.ratio
                                else:
                                    qty = line.quantity * -1

                            if inventory_entry_type:
                                # Create inventory ledger entries
                                source_price_purchase = 0
                                if record.entry_type == '4' and line.unit_of_measure.ratio > 0:
                                    # source_price_purchase = math.ceil(line.source_price / (line.unit_of_measure.ratio * line.quantity))
                                    source_price_purchase = math.ceil(line.total / (line.unit_of_measure.ratio * line.quantity)) #6 Aug 2024

                                self.env['ae.inventory.ledger.entry'].create({
                                    'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                                    'document_no': record.reference_no,
                                    'line_no': line.line_no,
                                    'inventory_id': line.inventory_name.id,
                                    'inventory_name': line.inventory_name.inventory_name,
                                    'document_type': '1',
                                    'inventory_type': line.inventory_name.inventory_type,
                                    'entry_type': inventory_entry_type,
                                    'inventory_label': line.inventory_name.inventory_label,
                                    'inventory_number': line.inventory_name.inventory_number,
                                    # 'inventory_group': line.inventory_name.inventory_group if line.inventory_name.inventory_group else False, 
                                    'asset_number': line.inventory_name.inventory_asset_number,
                                    'posting_date': record.posting_date,
                                    'location_code': line.inventory_location_code.location_code, 
                                    'room_code': line.inventory_room_code.room_code,
                                    'sub_room_code': line.inventory_sub_room_code.sub_room_code, 
                                    'quantity': line.quantity_returned if record.entry_type == '6' else qty,
                                    'unit_of_measure': line.unit_of_measure.name if line.unit_of_measure else False,
                                    'source_name': line.source_name,
                                    'source_price': line.total if record.entry_type == '4' else line.source_price, #6 Aug 2024
                                    'remarks': line.remarks,
                                    'qty_has_returned': line.quantity_returned,
                                    'source_no': line.document_no_inv_ledger,
                                    'qty_sales': line.quantity if record.entry_type == '5' else 0,
                                    'source_price_purchase': source_price_purchase,
                                    'ratio_purchase': (line.source_price/source_price_purchase) if record.entry_type == '4' else 0,
                                })

                                if record.entry_type == '5':
                                    inv_led_en = self.env['ae.inventory.ledger.entry'].search([('document_no', '=', record.reference_no), ('inventory_label', '=', line.inventory_label), ('entry_type', '=', '10')], order='entry_no desc', limit=1)
                                    inv_led_en.actual_qty = (inv_led_en.quantity*-1)

                                if record.entry_type == '6':
                                    inv_led_en = self.env['ae.inventory.ledger.entry'].search([('document_no', '=', line.document_no_inv_ledger), ('inventory_label', '=', line.inventory_label), ('entry_type', '=', '10')], order='entry_no desc', limit=1)
                                    inv_led_en.qty_sales -= line.quantity_returned


                                # Update inventory quantity based on entry type
                                if record.entry_type == '1' or record.entry_type == '4':
                                    line.inventory_name.inventory_qty = line.inventory_name.inventory_qty + qty
                                elif record.entry_type == '5':
                                    line.inventory_name.inventory_qty = line.inventory_name.inventory_qty + qty
                                elif record.entry_type == '6':
                                    line.inventory_name.inventory_qty = line.inventory_name.inventory_qty + qty
                                else:
                                    line.inventory_name.inventory_qty = line.inventory_name.inventory_qty - line.quantity

                                if record.entry_type == '4' and source_price_purchase > line.inventory_name.highest_source_price:
                                    line.inventory_name.highest_source_price = source_price_purchase
                                    
                            else:
                                raise ValidationError("No matching entry type found in the inventory ledger entry model for the selected itemjournal entry type!")
                        else:
                            raise ValidationError("Quantity must be greater than 0!")
                else:
                    raise ValidationError("Item Journal Lines are required!")
                
                if record.entry_type == '4' or record.entry_type == '5':
                    if record.item_journal_line_ids:
                        for line in record.item_journal_line_ids:
                            if line.source_price == 0:
                                raise ValidationError("Source Price can't be 0!")
                    else:
                        raise ValidationError("Item Journal Lines are required!")
                    
                if record.entry_type == '6':
                    if record.item_journal_line_ids:
                        for line in record.item_journal_line_ids:
                            if line.quantity_returned == 0:
                                raise ValidationError("Returned Quantity can't be 0!")
                    else:
                        raise ValidationError("Item Journal Lines are required!")

                # Change status to posted
                record.state = 'posted'

    def fnOpenWizard(self):
        if self.active == False:
            raise ValidationError("Cannot Get Data because this document is in Archive state!")
        else:
            return {
                'name': 'Sales Inventory Ledger Entries',
                'type': 'ir.actions.act_window',
                'res_model': 'ae.itemjournal.line.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_item_journal_header_id': self.id},
            }
    # Section function

class aeItemJournalLine(models.Model):
    _name = 'ae.itemjournal.line'
    _description = 'Item Journal Line'
    _order ='create_date desc'

    entry_no = fields.Integer(string='Entry No')
    item_journal_header_id = fields.Many2one('ae.itemjournal.header', string='Item Journal Header', ondelete='cascade')
    reference_no = fields.Char(string='Document No', store=True) #header
    line_no = fields.Integer(string='Line No',readonly=True,store=True, compute='_compute_line_no')
    posting_date = fields.Datetime(string='Posting Date', store=True)
    entry_type = fields.Selection([
        ('1', 'Stock In'),
        ('2', 'Stock Out'),
        ('3', 'Consumption'),
        ('4', 'Purchase'),
        ('5', 'Sales'),
        ('6', 'Sales Return'),
    ], string='Entry Type', related='item_journal_header_id.entry_type', store=True)
    item_type = fields.Selection([
        ('1', 'Attractive Items'),
        ('2', 'Stationery & Supplies'),
        ('3', 'Settling Kit'),
    ], string='Item Type', related='item_journal_header_id.item_type', store=True) #header
    inventory_name = fields.Many2one('ae.inventory', string='Inventory Name', required=True)
    
    inventory_qty = fields.Integer(string='Current Stock', store=True)

    inventory_label = fields.Char(string='Inventory Label', related='inventory_name.inventory_label', store=True)
    inventory_label_purchase = fields.Char(string='Inventory Label', store=True)
    inventory_label_attractive = fields.Char(string='Inventory Label', store=True)
    item_no = fields.Char(string='Item No') #inventory - inventory_number
    inventory_location_code = fields.Many2one('ae.location', string='Location Code', required=True, readonly=True, store=True)
    # inventory_room_code = fields.Many2one('ae.master.room', string='Room Code', domain="[('id', 'in', available_rooms)]", readonly=True, store=True)
    # inventory_sub_room_code = fields.Many2one('ae.master.sub.room', string='Sub Room Code', domain="[('id', 'in', available_sub_rooms)]", readonly=True, store=True)
    inventory_room_code = fields.Many2one('ae.master.room', string='Room Code',readonly=True, store=True)
    inventory_sub_room_code = fields.Many2one('ae.master.sub.room', string='Sub Room Code',readonly=True, store=True)
    
    available_rooms = fields.Many2many('ae.master.room', compute='_compute_available_rooms')
    available_sub_rooms = fields.Many2many('ae.master.sub.room', compute='_compute_available_sub_rooms')
    unit_of_measure = fields.Many2one('uom.uom', string='Unit of Measure', store=True)
    category_inventory_unit_of_measure = fields.Many2one('uom.category', string='Category Inventory Unit of Measure')
    remarks = fields.Char(string='Remarks')
    source_price = fields.Integer(string='Unit Price')
    quantity = fields.Integer(string='Quantity', required=True)
    required_field = fields.Boolean(string='Required', compute='_compute_required_field')
    source_name = fields.Char(string='Source Name', store=True)
    quantity_returned = fields.Integer(string='Quantity Returned')
    document_no_inv_ledger = fields.Char(string='Document No',store=True, readonly=True)
    total_source_price = fields.Integer(string='Total Source Price', compute='_compute_total_source_price')
    status_header = fields.Selection([('open', 'Open'), ('posted', 'Posted')], string='Status', related='item_journal_header_id.state', store=True)
    total = fields.Integer(string='Total', compute='_compute_total', readonly=True, store=True)

    # Section function

    @api.onchange('unit_of_measure')
    def _onchange_unit_of_measure(self):
        """
        This function is used to change unit of measure based on unit of measure"""
        for record in self:
            if record.unit_of_measure:
                if record.entry_type == '5':
                    record.source_price = record.inventory_name.highest_source_price * record.unit_of_measure.ratio

    def get_fields_to_ignore_in_search(self):
        return ['document_no_inv_ledger', 'inventory_label_attractive', 'inventory_label_purchase']
    
    def fields_get(self, allfields=None, attributes=None):
        res = super(aeItemJournalLine, self).fields_get(allfields=allfields, attributes=attributes)
        for field in self.get_fields_to_ignore_in_search():
            if res.get(field):
                res.get(field)['searchable'] = False
        return res

    @api.depends('quantity', 'source_price')
    def _compute_total(self):
        for record in self:
            record.total = record.quantity * record.source_price

    @api.onchange('inventory_label_purchase')
    def _onchange_inventory_label_purchase(self):
        for record in self:
            if record.inventory_label_purchase:
                inventory = self.env['ae.inventory'].search([('inventory_label', '=', record.inventory_label_purchase)])
                if inventory:
                    record.inventory_name = inventory.id
                else:
                    raise ValidationError("Inventory with label %s is not found in the system!" % record.inventory_label)
                
    @api.onchange('inventory_label_attractive')
    def _onchange_inventory_label_attractive(self):
        for record in self:
            if record.inventory_label_attractive:
                inventory = self.env['ae.inventory'].search([('inventory_label', '=', record.inventory_label_attractive)])
                if inventory:
                    record.inventory_name = inventory.id
                else:
                    raise ValidationError("Inventory with label %s is not found in the system!" % record.inventory_label)

    @api.depends('quantity', 'source_price')
    def _compute_total_source_price(self):
        for record in self:
            record.total_source_price = record.quantity * record.source_price

    @api.onchange('quantity')
    def _onchange_quantity(self):
        for record in self:
            if record.item_journal_header_id.entry_type in ('2', '3'):
                if record.quantity > record.inventory_name.inventory_qty:
                    raise ValidationError("Quantity must be less than or equal to the available quantity in the inventory! Now available: %s" % record.inventory_name.inventory_qty)
                
            if record.item_journal_header_id.entry_type == '5':
                if record.unit_of_measure == record.inventory_name.inventory_unit_of_measure:
                    if record.quantity > record.inventory_name.inventory_qty:
                        raise ValidationError("Quantity must be less than or equal to the available quantity in the inventory! Now available: %s" % record.inventory_name.inventory_qty)
                else:
                    qty = record.quantity * record.unit_of_measure.ratio
                    if qty > record.inventory_name.inventory_qty:
                        raise ValidationError("Quantity must be less than or equal to the available quantity in the inventory! In Journal Line: %s, Inventory Stock: %s for %s" % (qty, record.inventory_name.inventory_qty, record.inventory_name.inventory_name))
                    
                
    @api.onchange('quantity_returned')
    def _onchange_quantity_returned(self):
        for record in self:
            if record.quantity_returned > record.quantity:
                raise ValidationError("Quantity Returned must be less than or equal to the quantity!")

    @api.depends('entry_type')
    def _compute_required_field(self):
        """
        If Entry Type is Stock in/out, Required Field will be True"""
        for record in self:
            if record.entry_type in ('1', '2'):
                record.required_field = True
            else:
                record.required_field = False

    @api.onchange('item_journal_header_id')
    def _onchange_item_journal_header_id(self):
        for record in self:
            record.reference_no = record.item_journal_header_id.reference_no
            record.posting_date = record.item_journal_header_id.posting_date
            record.entry_type = record.item_journal_header_id.entry_type
            record.item_type = record.item_journal_header_id.item_type
            if record.item_journal_header_id.vendor_name:
                record.source_name = record.item_journal_header_id.vendor_name.vendor_name
            elif record.item_journal_header_id.customer_name:
                record.source_name = record.item_journal_header_id.customer_name.customer_name

    @api.onchange('inventory_name')
    def _onchange_inventory_name(self):
        """
        This function is used to get item no from inventory"""
        for record in self:
            record.item_no = record.inventory_name.inventory_number
            record.inventory_label_purchase = record.inventory_name.inventory_label
            record.inventory_label_attractive = record.inventory_name.inventory_label
            record.inventory_location_code = record.inventory_name.inventory_location_code
            record.inventory_room_code = record.inventory_name.inventory_room_code
            record.inventory_sub_room_code = record.inventory_name.inventory_sub_room_code
            # record.unit_of_measure = record.inventory_name.inventory_unit_of_measure
            record.category_inventory_unit_of_measure = record.inventory_name.inventory_unit_of_measure.category_id
            record.inventory_qty = record.inventory_name.inventory_qty
            if record.item_journal_header_id.entry_type == '5':
                record.source_price = record.inventory_name.highest_source_price
                if record.inventory_name.sales_uom:
                    record.unit_of_measure = record.inventory_name.sales_uom
                else:
                    record.unit_of_measure = record.inventory_name.inventory_unit_of_measure
                # record.unit_of_measure = record.inventory_name.sales_uom
            elif record.item_journal_header_id.entry_type == '4':
                # record.unit_of_measure = record.inventory_name.purchase_uom
                if record.inventory_name.purchase_uom:
                    record.unit_of_measure = record.inventory_name.purchase_uom
                else:
                    record.unit_of_measure = record.inventory_name.inventory_unit_of_measure
            else:
                record.unit_of_measure = record.inventory_name.inventory_unit_of_measure
                

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

    @api.depends('item_journal_header_id.item_journal_line_ids')
    def _compute_line_no(self):
        for record in self:
            record.line_no = 0
            for line in record.item_journal_header_id.item_journal_line_ids:
                if line.id == record.id:
                    record.line_no += 1
                    break
                else:
                    record.line_no += 1

    # Raise error when entry type is purchase and vendor in header is empty (onchange)
    @api.onchange('item_journal_header_id', 'item_journal_header_id.vendor_name')
    def _onchange_vendor_name(self):
        for record in self:
            if record.item_journal_header_id.entry_type == '4':
                if not record.item_journal_header_id.vendor_name:
                    raise ValidationError("Vendor Name is required!")
            elif record.item_journal_header_id.entry_type == '5':
                if not record.item_journal_header_id.customer_name:
                    raise ValidationError("Customer Name is required!")
    # Section function

class journal_sales_wizard(models.TransientModel):
    _name = 'ae.itemjournal.line.wizard'
    _description = 'Item Journal Line Wizard'

    inv_led_en = fields.Many2many('ae.inventory.ledger.entry', string='Inventory Ledger Entry', domain="[('entry_type', '=', '10'), ('qty_sales', '>', 0)]")

    # Insert selected data from Inventory Ledger Entry to Item Journal Line
    def insert_item_journal_line(self):
        for record in self:
            for line in record.inv_led_en:
                self.env['ae.itemjournal.line'].create({
                    'item_journal_header_id': self.get_item_journal_header_id().id,
                    'document_no_inv_ledger': line.document_no,
                    'inventory_name': self.env['ae.inventory'].search([('inventory_name', '=', line.inventory_name)]).id,
                    'inventory_location_code': self.env['ae.location'].search([('location_code', '=', line.location_code)]).id,
                    'unit_of_measure': self.env['uom.uom'].search([('name', '=', line.unit_of_measure)], limit=1).id,
                    'remarks': line.remarks,
                    # 'quantity': line.quantity * -1,
                    'quantity': line.qty_sales,
                    'source_price': line.source_price,
                    'posting_date': self.get_item_journal_header_id().posting_date,
                    'reference_no': self.get_item_journal_header_id().reference_no,
                    'source_name': line.source_name,
                })

    def get_item_journal_header_id(self):
        return self.env['ae.itemjournal.header'].browse(self._context.get('active_id'))


        