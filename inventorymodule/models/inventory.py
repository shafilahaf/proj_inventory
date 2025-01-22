from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import base64
from lxml import etree

class inventory_master_group(models.Model):
    _name = 'ae.inventory.master.group'
    _description = 'Inventory Master Group'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    level = fields.Integer(string='Level')
    active = fields.Boolean(default=True)
    name = fields.Char(string='Name', required=True)
    picture = fields.Binary(string='Picture', attachment=True)
    inventories = fields.One2many('ae.inventory', 'inventory_group', string='Inventories')

    # <!-- 2/26/2024 -->
    group_type = fields.Char(string='Group Type')
    # <!-- 2/26/2024 -->

    # Uppercase Name
    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name = self.name.upper().replace(" ", "")

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if rec.name:
                if rec.search([('name', '=', rec.name), ('id', '!=', rec.id)]):
                    raise ValidationError(_('Name must be unique!'))
                
    @api.constrains('level')
    def _check_level(self):
        for rec in self:
            if rec.level:
                if rec.search([('level', '=', rec.level), ('id', '!=', rec.id)]):
                    raise ValidationError(_('Level must be unique!'))

class inventory(models.Model):
    _name = 'ae.inventory'
    _description = 'Inventory'
    _rec_name = 'inventory_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('inventory_label_unique', 'unique(inventory_label)', 'Inventory Label must be unique!'),
        ('inventory_serial_number_unique', 'unique(inventory_serial_number)', 'Serial Number must be unique!')
    ]
    _order = 'inventory_name asc'

    active = fields.Boolean(default=True)
    inventory_create_date = fields.Date(string='Create Date', default=fields.Date.today())
    inventory_picture = fields.Binary(string='Picture', attachment=True)
    inventory_type = fields.Selection([
        ('1', 'Inventory'),
        ('2', 'Asset'),
        ('3', 'Attractive Items'),
        ('4', 'Stationary & Supplies'),
        ('5', 'Settling Kit'),
    ], string='Type')

    inventory_type_inventory = fields.Selection([('1', 'Inventory'), ('2', 'Asset')],string='Type')
    inventory_type_attractive = fields.Selection([('3', 'Attractive Items')], string='Type', default='3')
    inventory_type_setkits = fields.Selection([('5', 'Settling Kit')], string='Type', default='5')
    inventory_type_stationary_supplies = fields.Selection([('4', 'Stationary & Supplies')], string='Type', default='4')
    inventory_qty = fields.Integer(string='Quantity', store=True)
    inventory_code = fields.Char(string='Code', size=20)
    inventory_number = fields.Char(string='Number', size=20)
    inventory_label = fields.Char(string='Label', required=True)
    inventory_name = fields.Char(string='Name', required=True)
    # inventory_status = fields.Selection([
    #     ('1', 'Active'),
    #     ('2', 'Write-Off'),
    #     ('3', 'Auction'),
    #     ('4', 'Destroyed'),
    # ], string='Status', default='1')
    inventory_status = fields.Selection([
        ('1', 'Active'),
        ('2', 'Disposed'),
    ], string='Status', default='1', readonly=True)
    inventory_acquisition_value = fields.Integer(string='Acquisition Value')
    inventory_acquisition_date = fields.Date(string='Acquisition Date')
    inventory_group = fields.Many2one('ae.inventory.master.group', string='Group Inventory')
    inventory_group_level = fields.Integer(string='Group Level', related='inventory_group.level', store=True)
    inventory_height = fields.Integer(string='Height')
    inventory_width = fields.Integer(string='Width')
    inventory_length = fields.Integer(string='Length')
    inventory_serial_number = fields.Char(string='Serial Number')
    inventory_unit_of_measure = fields.Many2one('uom.uom', string='Unit of Measure')
    inventory_remarks = fields.Text(string='Remarks')
    inventory_asset_number = fields.Char(string='Asset Number')
    inventory_electrical = fields.Boolean(string='Electrical')
    inventory_test_date = fields.Date(string='Test Date')
    inventory_expired_date = fields.Date(string='Expired Date')
    inventory_tagging_id = fields.Char(string='Tagging ID')
    inventory_tagger_name = fields.Char(string='Tagger Name')
    inventory_old_location = fields.Char(string='Old Location', readonly=True)
    inventory_location_code = fields.Many2one('ae.location', string='Location Code')
    inventory_room_code = fields.Many2one('ae.master.room', string='Room Code', domain="[('id', 'in', available_rooms)]")
    inventory_sub_room_code = fields.Many2one('ae.master.sub.room', string='Sub Room Code', domain="[('id', 'in', available_sub_rooms)]")
    available_rooms = fields.Many2many('ae.master.room', compute='_compute_available_rooms')
    available_sub_rooms = fields.Many2many('ae.master.sub.room', compute='_compute_available_sub_rooms')
    inventory_room_name = fields.Char(string='Room Name', related='inventory_room_code.room_name', store=True)
    inventory_room_subroom_name = fields.Char(string='Sub Room Name', related='inventory_sub_room_code.sub_room_name', store=True)
    inventory_settling_master_group = fields.Many2one('ae.settling.master.group', string='Group Settling Kit')
    
    inventory_location_name = fields.Char(string='Location Name', store=True)

    highest_source_price = fields.Integer(string='Source Price', store=True, track_visibility='always') # Compute perlu dimatikan ketika import data stationery excel #, compute='_compute_highest_source_price'
    minimum_qty_level = fields.Integer(string='Minimum Qty Level')
    stock_warning = fields.Boolean(string='Stock Warning', compute='_compute_stock_warning', store=True, readonly=True)

    sales_price = fields.Integer(string='Sales Price')

    last_vendor = fields.Char(string='Last Vendor')
    
    # invledent_last_scan_update = fields.Date(string='Last Scan Update', compute='_compute_last_scan_update', store=True)
    # invledent_last_update_by_user = fields.Many2one('res.users', string='Last Scan By User', compute='_compute_last_update_by_user', store=True)

    last_scan_update = fields.Datetime(string='Last Scan Update', store=True)
    last_update_by_user = fields.Many2one('res.users', string='Last Scan By User', store=True)

    return_quantity = fields.Integer(string='Return Quantity')
    tenant_name = fields.Char(string='Tenant Name')
    delivery_date = fields.Date(string='Delivery Date')

    invledent = fields.One2many('ae.inventory.ledger.entry', 'inventory_id', string='Inventory Ledger', domain=[('entry_type', '=', '9')])
    inventory_ledger_entries = fields.One2many('ae.inventory.ledger.entry', 'inventory_id', string='Inventory Ledger Entries')
    disposal_method = fields.Selection([
        ('1', 'Write-Off'),
        ('2', 'Auction'),
        ('3', 'Destroyed'),
    ], string='Disposal Method')

    inventory_qty_on_loan = fields.Integer(string='Qty on loan', compute='_compute_inventory_qty_on_loan', store=True, readonly=True)
    inventory_qty_on_loss = fields.Integer(string='Qty on loss', compute='_compute_inventory_qty_on_loss', store=True, readonly=True)

    qty_out_from_inventory_ledger = fields.Integer(string='Qty Out', compute='_compute_qty_out_from_inventory_ledger', store=True, readonly=True)
    qty_in_from_inventory_ledger = fields.Integer(string='Qty In', compute='_compute_qty_in_from_inventory_ledger', store=True, readonly=True)

    category_inventory_unit_of_measure = fields.Many2one('uom.category', string='Category Inventory Unit of Measure')
    purchase_uom = fields.Many2one('uom.uom', string='Purchase UoM', domain="[('category_id', '=', category_inventory_unit_of_measure)]")
    sales_uom = fields.Many2one('uom.uom', string='Sales UoM', domain="[('category_id', '=', category_inventory_unit_of_measure)]")
    ratio_purchase_uom = fields.Float(string='Ratio Purchase UoM')
    ratio_sales_uom = fields.Float(string='Ratio Sales UoM')
    ratio_uom = fields.Float(string='Ratio UoM')

    
    # Section for Function

    @api.onchange('inventory_unit_of_measure')
    def _onchange_inventory_unit_of_measure(self):
        if self.inventory_unit_of_measure:
            self.ratio_uom = self.inventory_unit_of_measure.ratio
            self.category_inventory_unit_of_measure = self.inventory_unit_of_measure.category_id

    @api.onchange('purchase_uom')
    def _onchange_purchase_uom(self):
        if self.purchase_uom:
            self.ratio_purchase_uom = self.purchase_uom.ratio
    @api.onchange('sales_uom')
    def _onchange_sales_uom(self):
        if self.sales_uom:
            self.ratio_sales_uom = self.sales_uom.ratio

    # Button to fill inventory_location_name from inventory_location_code
    def fill_inventory_location_name(self):
        for record in self:
            record.inventory_location_name = record.inventory_location_code.location_name

    # Uppercase Inventory Label
    @api.onchange('inventory_label')
    def _onchange_inventory_label(self):
        if self.inventory_label:
            self.inventory_label = self.inventory_label.upper().replace(" ", "")

    # Uppercase Inventory Code
    @api.onchange('inventory_code')
    def _onchange_inventory_code(self):
        if self.inventory_code:
            self.inventory_code = self.inventory_code.upper().replace(" ", "")
            # Cannot duplicate inventory_code
            # inventory_code = self.env['ae.inventory'].search([('inventory_code', '=', self.inventory_code)])
            # if len(inventory_code) > 1:
            #     raise ValidationError('Inventory Code already exist! Please use another Inventory Code.')

    # Uppercase Inventory Serial Number
    @api.onchange('inventory_serial_number')
    def _onchange_inventory_serial_number(self):
        if self.inventory_serial_number:
            self.inventory_serial_number = self.inventory_serial_number.upper().replace(" ", "")

    # Uppercase Tagging ID
    @api.onchange('inventory_tagging_id')
    def _onchange_inventory_tagging_id(self):
        if self.inventory_tagging_id:
            self.inventory_tagging_id = self.inventory_tagging_id.upper().replace(" ", "")
            # Cannot duplicate inventory_tagging_id
            # inventory_tagging_id = self.env['ae.inventory'].search([('inventory_tagging_id', '=', self.inventory_tagging_id)])
            # if len(inventory_tagging_id) > 1:
            #     raise ValidationError('Tagging ID already exist! Please use another Tagging ID.')

    # Uppercase Asset Number
    @api.onchange('inventory_asset_number')
    def _onchange_inventory_asset_number(self):
        if self.inventory_asset_number:
            self.inventory_asset_number = self.inventory_asset_number.upper().replace(" ", "")

    # Cannot duplicate inventory_label
    # @api.constrains('inventory_label')
    # def _check_inventory_label(self):
    #     for record in self:
    #         if record.active == True:
    #             inventory_label = self.env['ae.inventory'].search([('inventory_label', '=', record.inventory_label)])
    #             if len(inventory_label) > 1:
    #                 raise ValidationError('Inventory Label already exist! Please use another Inventory Label.')

    # Remarks size validation (max 50 characters)
    @api.constrains('inventory_remarks')
    def _check_inventory_remarks(self):
        for record in self:
            # if len(record.inventory_remarks) > 50:
            #     raise ValidationError('Remarks must be less than 50 characters!')
            if record.inventory_remarks:
                if len(record.inventory_remarks) > 100:
                    raise ValidationError('Remarks must be less than 100 characters!')
                

    @api.depends('inventory_qty', 'minimum_qty_level')
    def _compute_stock_warning(self):
        for inventory in self:
            # Di settling kit jumlah qty on hand + qty onloan, kalo < minimum qty terchecklist
            if inventory.inventory_type == '5':
                if inventory.inventory_qty + inventory.inventory_qty_on_loan < inventory.minimum_qty_level:
                    inventory.stock_warning = True
                else:
                    inventory.stock_warning = False
            else:
                if inventory.inventory_qty < inventory.minimum_qty_level:
                    inventory.stock_warning = True
                else:
                    inventory.stock_warning = False

            # if inventory.inventory_qty < inventory.minimum_qty_level:
            #     inventory.stock_warning = True
            # else:
            #     inventory.stock_warning = False

    @api.depends('inventory_ledger_entries')
    def _compute_qty_out_from_inventory_ledger(self):
        """
        Compute the qty out from inventory ledger entries (quantity < 0)
        """
        for inventory in self:
            qty_filtered = inventory.inventory_ledger_entries.filtered(lambda r: r.quantity < 0 and r.entry_type in ['3', '8', '10', '12', '6', '7', '17'])
            inventory.qty_out_from_inventory_ledger = sum(qty_filtered.mapped('quantity'))


    @api.depends('inventory_ledger_entries')
    def _compute_qty_in_from_inventory_ledger(self):
        """
        Compute the qty in from inventory ledger entries (quantity > 0)
        """
        for inventory in self:
            qty_in_entries = inventory.inventory_ledger_entries.filtered(lambda r: r.quantity > 0 and r.entry_type in ['2', '9', '11'])
            qty_in_entries_return = inventory.inventory_ledger_entries.filtered(lambda r: r.return_quantity > 0 and r.entry_type in ['16'])
            inventory.qty_in_from_inventory_ledger = sum(qty_in_entries.mapped('quantity')) + sum(qty_in_entries_return.mapped('return_quantity'))

    def action_viewqty_in(self):
        return {
            'name': _('Qty In'),
            'domain': [('id', 'in', self.inventory_ledger_entries.filtered(lambda r: r.quantity > 0 and r.entry_type in ['2', '9', '11', '16']).ids)],
            'res_model': 'ae.inventory.ledger.entry',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
        }
    
    def action_viewqty_out(self):
        return {
            'name': _('Qty Out'),
            'domain': [('id', 'in', self.inventory_ledger_entries.filtered(lambda r: r.quantity < 0 and r.entry_type in ['3', '8', '10', '12', '6', '7', '17']).ids)],
            'res_model': 'ae.inventory.ledger.entry',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
        }

    @api.depends('inventory_ledger_entries')
    def _compute_inventory_qty_on_loan(self):
        for inventory in self:
            loan_entries = inventory.inventory_ledger_entries.filtered(lambda r: r.entry_type == '12' and r.quantity > 0)
            return_entries = inventory.inventory_ledger_entries.filtered(lambda r: r.entry_type == '16' and r.return_quantity < 0)
            loss_entreis = inventory.inventory_ledger_entries.filtered(lambda r: r.entry_type == '13' and r.quantity < 0)
            inventory.inventory_qty_on_loan = sum(loan_entries.mapped('quantity')) + sum(return_entries.mapped('return_quantity')) + sum(loss_entreis.mapped('quantity'))

    @api.depends('inventory_ledger_entries')
    def _compute_inventory_qty_on_loss(self):
        for inventory in self:
            loss_entreis = inventory.inventory_ledger_entries.filtered(lambda r: r.entry_type == '13' and r.quantity < 0)
            inventory.inventory_qty_on_loss = sum(loss_entreis.mapped('quantity'))

    @api.depends('inventory_ledger_entries')
    def _compute_last_scan_update(self):
        for inventory in self:
            movement_entries = inventory.inventory_ledger_entries.filtered(lambda r: r.entry_type == '4')  # Filter by "Movement" entry_type
            last_entry = movement_entries.sorted(key=lambda r: r.updated_date, reverse=True)
            if last_entry:
                inventory.invledent_last_scan_update = last_entry[0].updated_date
            else:
                inventory.invledent_last_scan_update = False

    @api.depends('inventory_ledger_entries')
    def _compute_last_update_by_user(self):
        for inventory in self:
            movement_entries = inventory.inventory_ledger_entries.filtered(lambda r: r.entry_type == '4')  # Filter by "Movement" entry_type
            last_entry = movement_entries.sorted(key=lambda r: r.updated_date, reverse=True)
            if last_entry:
                inventory.invledent_last_update_by_user = last_entry[0].updated_by
            else:
                inventory.invledent_last_update_by_user = False

    # @api.depends('inventory_ledger_entries')
    # def _compute_highest_source_price(self):
    #     for inventory in self:
    #         purchase_entries = inventory.inventory_ledger_entries.filtered(lambda r: r.entry_type == '9') # Filter by "Purchase" entry_type
    #         for entry in purchase_entries:
    #             if max(purchase_entries.mapped('source_price')) > inventory.highest_source_price: #entry.source_price > highest_price or 
    #                 self.highest_source_price = max(purchase_entries.mapped('source_price'))
    #             elif max(purchase_entries.mapped('source_price')) < inventory.highest_source_price:
    #                 self.highest_source_price = inventory.highest_source_price

    # @api.depends('inventory_ledger_entries')
    # def _compute_highest_source_price(self):
    #     for inventory in self:
    #         purchase_entries = inventory.inventory_ledger_entries.filtered(lambda r: r.entry_type == '9') # Filter by "Purchase" entry_type
    #         for entry in purchase_entries:
    #             if max(purchase_entries.mapped('source_price_purchase')) > inventory.highest_source_price:
    #                 self.highest_source_price = max(purchase_entries.mapped('source_price_purchase'))
    #             elif max(purchase_entries.mapped('source_price_purchase')) < inventory.highest_source_price:
    #                 self.highest_source_price = inventory.highest_source_price



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

    @api.onchange('inventory_type')
    def _onchange_inventory_type(self):
        """
        This method is called when inventory_type is changed."""
        if self.inventory_type == '1' or self.inventory_type == '2':
            self.inventory_qty = 1

    @api.onchange('inventory_number')
    def _onchange_inventory_number(self):
        """
        This method is called when inventory_number is changed."""
        if self.inventory_number:
            self.inventory_number = self.inventory_number.upper().replace(" ", "")

    @api.constrains('inventory_serial_number')
    def _check_inventory_serial_number(self):
        """
        Check if inventory_serial_number is unique."""
        if self.inventory_serial_number:
            inventory_serial_number = self.env['ae.inventory'].search([('inventory_serial_number', '=', self.inventory_serial_number)])
            if len(inventory_serial_number) > 1:
                raise ValidationError('Serial Number already exist! Please use another Serial Number.')

    @api.onchange('inventory_type_attractive')
    def _onchange_inventory_type_attractive(self):
        """
        This method is called when inventory_type_attractive is changed."""
        if self.inventory_type_attractive == '3':
            self.inventory_type = '3'

    @api.onchange('inventory_type_setkits')
    def _onchange_inventory_type_setkits(self):
        """
        This method is called when inventory_type_setkits is changed."""
        if self.inventory_type_setkits == '5':
            self.inventory_type = '5'

    @api.onchange('inventory_type_stationary_supplies')
    def _onchange_inventory_type_stationary_supplies(self):
        """
        This method is called when inventory_type_stationary_supplies is changed."""
        if self.inventory_type_stationary_supplies == '4':
            self.inventory_type = '4'

    @api.onchange('inventory_type_inventory')
    def _onchange_inventory_type_inventory(self):
        """
        This method is called when inventory_type_inventory is changed."""
        if self.inventory_type_inventory == '1':
            self.inventory_type = '1'
        elif self.inventory_type_inventory == '2':
            self.inventory_type = '2'
            
    # def _get_matching_inventory_entry_type(self, status):
    #     """
    #     Map the entry types between status.
    #     """
    #     status_mapping = {
    #         '1': '15',  # Active
    #         '2': '6',  # Write-Off
    #         '3': '5',  # Auction
    #         '4': '7',  # Destroyed
    #     }
    
    @api.model
    def create(self, vals):
        # Log the action

        # action_description = f"Inventory {vals['inventory_name']} created"
        # action_description inventory_name - inventory_label 
        action_description = f"Inventory {vals['inventory_name']} - {vals['inventory_label']} created"

        # Module based on inventory_type
        if vals['inventory_type'] == '1':
            module = "Inventory"
        elif vals['inventory_type'] == '2':
            module = "Inventory"
        elif vals['inventory_type'] == '3':
            module = "Attractive Items"
        elif vals['inventory_type'] == '4':
            module = "Stationary & Supplies"
        elif vals['inventory_type'] == '5':
            module = "Settling Kit"

        self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, module)

        return super(inventory, self).create(vals)

    def write(self, vals):
        # Initialize a list to store updated fields for each record
        updated_fields_list = []

        # Mapping between field names in the code and display names in the action description
        field_name_mapping = {
            'inventory_name': 'Name',
            'inventory_label': 'Label',
            'inventory_type': 'Type',
            'inventory_qty': 'Quantity',
            'inventory_code': 'Code',
            'inventory_number': 'Number',
            'inventory_status': 'Status',
            'inventory_acquisition_value': 'Acquisition Value',
            'inventory_acquisition_date': 'Acquisition Date',
            'inventory_group': 'Group Inventory',
            'inventory_height': 'Height',
            'inventory_width': 'Width',
            'inventory_length': 'Length',
            'inventory_serial_number': 'Serial Number',
            'inventory_unit_of_measure': 'Unit of Measure',
            'inventory_remarks': 'Remarks',
            'inventory_asset_number': 'Asset Number',
            'inventory_electrical': 'Electrical',
            'inventory_test_date': 'Test Date',
            'inventory_expired_date': 'Expired Date',
            'inventory_tagging_id': 'Tagging ID',
            'inventory_tagger_name': 'Tagger Name',
            'inventory_old_location': 'Old Location',
            'inventory_location_code': 'Location Code',
            'inventory_room_code': 'Room Code',
            'inventory_sub_room_code': 'Sub Room Code',
            'inventory_room_name': 'Room Name',
            'inventory_room_subroom_name': 'Sub Room Name',
            'inventory_settling_master_group': 'Group Settling Kit',
            'inventory_location_name': 'Location Name',
            'highest_source_price': 'Source Price',
            'minimum_qty_level': 'Minimum Qty Level',
            'sales_price': 'Sales Price',
            'last_vendor': 'Last Vendor',
            'return_quantity': 'Return Quantity',
            'tenant_name': 'Tenant Name',
            'delivery_date': 'Delivery Date',
            'disposal_method': 'Disposal Method',

        }

        for record in self:
            # Identify which fields are updated in the current record
            updated_fields = [field for field in record._fields if field in vals]

            # Create a dictionary to store old and new values for each updated field
            old_new_values = {}
            for field in updated_fields:
                old_value = getattr(record, field)
                # Use vals.get(field, old_value) to get the display name
                new_value = vals.get(field, old_value)

                # Convert Many2one field value to its display name
                if field in field_name_mapping and isinstance(old_value, models.Model):
                    old_value = old_value.display_name
                if field in field_name_mapping and isinstance(new_value, models.Model):
                    new_value = new_value.display_name

                # Use the display name from the mapping
                display_name = field_name_mapping.get(field, field)
                old_new_values[display_name] = {'Old': old_value, 'New': new_value}

            # Construct the action description for each record
            action_description = f"Fields {old_new_values} updated for Inventory {record.inventory_name} - {record.inventory_label}"

            # Call the super method to perform the actual write for the current record
            res = super(inventory, record).write(vals)

            updated_fields_list.append(action_description)

        # Map inventory_type to module names
        inventory_type_to_module = {
            '1': "Inventory",
            '2': "Inventory",
            '3': "Attractive Items",
            '4': "Stationary & Supplies",
            '5': "Settling Kit"
        }

        # Determine the module based on inventory_type (assuming it's the same for all selected records)
        default_module = "Unknown Module"
        module = inventory_type_to_module.get(self[0].inventory_type, default_module)

        # Create a user log for each record updated
        for action_description in updated_fields_list:
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, module)

        return True  # Return True to indicate success
    
    def unlink(self):
        for record in self:
            action_description = f"Inventory {record.inventory_name} - {record.inventory_label} deleted"
            # Module based on inventory_type
            if record.inventory_type == '1':
                module = "Inventory"
            elif record.inventory_type == '2':
                module = "Inventory"
            elif record.inventory_type == '3':
                module = "Attractive Items"
            elif record.inventory_type == '4':
                module = "Stationary & Supplies"
            elif record.inventory_type == '5':
                module = "Settling Kit"

            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, module)
        return super(inventory, self).unlink()

    # Hide Filter dropdown for Inventory Type
    def get_fields_to_ignore_in_search(self):
        return ['inventory_type_inventory', 'inventory_type_attractive', 'inventory_type_setkits', 'inventory_type_stationary_supplies', 'inventory_group_level']
    
    def fields_get(self, allfields=None, attributes=None):
        res = super(inventory, self).fields_get(allfields=allfields, attributes=attributes)
        for field in self.get_fields_to_ignore_in_search():
            if res.get(field):
                res.get(field)['searchable'] = False
        return res


    
    # Section for Function
    