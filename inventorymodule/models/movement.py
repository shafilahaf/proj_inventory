from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class aeMovementHeader(models.Model):
    _name = 'ae.movement.header'
    _description = 'Movement Header'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'document_no'
    _order = 'posting_date desc'

    active = fields.Boolean(default=True)
    posting_date = fields.Datetime(string='Posting Date',default=fields.Datetime.now, required=True)
    document_no = fields.Char(string='Document No', required=True, readonly=True, default='New')
    entry_type = fields.Selection([('1', 'Movement')], string='Entry Type', required=True, default='1', readonly=True)
    status = fields.Selection([('open', 'Open'), ('posted', 'Posted')], string='Status', required=True, default='open')
    user = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user, readonly=True)
    inventory_location_code = fields.Many2one('ae.location', string='Location Code', required=True)
    inventory_room_code = fields.Many2one('ae.master.room', string='Room Code', domain="[('id', 'in', available_rooms)]")
    inventory_sub_room_code = fields.Many2one('ae.master.sub.room', string='Sub Room Code', domain="[('id', 'in', available_sub_rooms)]")
    movement_line = fields.One2many('ae.movement.line', 'header_id', string='Movement Line')
    available_rooms = fields.Many2many('ae.master.room', compute='_compute_available_rooms')
    available_sub_rooms = fields.Many2many('ae.master.sub.room', compute='_compute_available_sub_rooms')

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

    def action_posting_invle(self):
        """
        This function is used to create posting action button for inserting data to inventory ledger entries"""
        for record in self:
            if record.movement_line:
                for line in record.movement_line:
                    if line.quantity > 0:
                        # create inventory ledger entries
                        self.env['ae.inventory.ledger.entry'].create({
                            'entry_no': self.env['ae.inventory.ledger.entry'].search([], order='entry_no desc', limit=1).entry_no + 1,
                            'inventory_name': line.inventory.inventory_name,
                            'document_type': "4",
                            'inventory_type': line.inventory.inventory_type,
                            'inventory_label': line.inventory.inventory_label,
                            'inventory_number': line.inventory.inventory_number,
                            'asset_number': line.inventory.inventory_asset_number,
                            'posting_date': record.posting_date,
                            'from_location_code': line.from_location.id,
                            'to_location_code': line.to_location.id,
                            'remarks': line.remarks,
                            'document_no': record.document_no,
                            'location_code': record.inventory_location_code.location_code,
                            'room_code': record.inventory_room_code.id,
                            'sub_room_code': record.inventory_sub_room_code.id,
                        })
                    else:
                        raise ValidationError("Quantity must be greater than 0!")
            else:
                raise ValidationError("Item Journal Lines are required!")
            
            # change status to posted
            record.status = 'posted'

            for line in record.movement_line:
                # Write new location to inventory master
                self.env['ae.inventory'].search([('id', '=', line.inventory.id)]).write({
                    'inventory_location_code': line.to_location.id,
                    'inventory_room_code': line.to_room.id,
                    'inventory_sub_room_code': line.to_sub_room.id,
                    # 'inventory_location_name': self.env['ae.location'].search([('id', '=', line.to_location.id)]).location_name,
                    'last_scan_update': record.posting_date,
                    'last_update_by_user': record.user.id,
                    'inventory_remarks': line.remarks,
                    # 'inventory_old_location': line.from_location.id,
                })
            
    @api.onchange('movement_line')
    def _onchange_movement_line(self):
        # Cannot duplicate inventory
        for record in self:
            if record.movement_line:
                inventory_list = []
                for line in record.movement_line:
                    if line.inventory.inventory_label in inventory_list:
                        raise ValidationError("Inventory with label %s is entered more than once!" % line.inventory.inventory_label)
                    else:
                        inventory_list.append(line.inventory.inventory_label)

    @api.model
    def create(self, vals):
        """
        This function is used to override create method to generate document no
        """
        if vals.get('document_no', 'New') == 'New':
            vals['document_no'] = self.env['ir.sequence'].next_by_code('ae.movement.header') or 'New'
        result = super(aeMovementHeader, self).create(vals)
        return result

    def unlink(self):
        """
        This function is used to prevent delete record
        """
        for record in self:
            if record.status == 'posted':
                raise ValidationError("Cannot delete posted record!")
        return super(aeMovementHeader, self).unlink()   

class aeMovementLine(models.Model):
    _name = 'ae.movement.line'
    _description = 'Movement Line'
    
   
    header_id = fields.Many2one('ae.movement.header', string='Header ID', ondelete='cascade')
    entry_type = fields.Selection([('1', 'Movement')], string='Entry Type', related='header_id.entry_type', store=True)
    inventory = fields.Many2one('ae.inventory', string='Inventory', required=True)
    inventory_label = fields.Char(string='Inventory Label', store=True)
    inventory_number = fields.Char(string='Inventory Number', related='inventory.inventory_number', store=True)
    asset_number = fields.Char(string='Asset Number', related='inventory.inventory_asset_number', store=True)
    # inventory_label = fields.Char(string='Inventory Label', related='inventory.inventory_label', store=True)
    inventory_name = fields.Char(string='Inventory Name', related='inventory.inventory_name', store=True)
    from_location = fields.Many2one('ae.location', string='From Location', store=True, readonly=True, related='inventory.inventory_location_code')
    from_room = fields.Many2one('ae.master.room', string='From Room', store=True, readonly=True, related='inventory.inventory_room_code')
    from_sub_room = fields.Many2one('ae.master.sub.room', string='From Sub Room', store=True, readonly=True, related='inventory.inventory_sub_room_code')
    to_location = fields.Many2one('ae.location', string='To Location', related='header_id.inventory_location_code', store=True)
    to_room = fields.Many2one('ae.master.room', string='To Room', related='header_id.inventory_room_code', store=True)
    to_sub_room = fields.Many2one('ae.master.sub.room', string='To Sub Room', related='header_id.inventory_sub_room_code', store=True)
    remarks = fields.Char(string='Remarks')
    inventory_picture = fields.Binary(string='Inventory Picture', related='inventory.inventory_picture', store=True)
    quantity = fields.Integer(string='Quantity', default=1, required=True)
    uom = fields.Many2one('uom.uom', string='Unit of Measure', store=True, readonly=True, related='inventory.inventory_unit_of_measure')
    create_by = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    create_scan_date = fields.Datetime(string='Scan Datetime', readonly=True, store=True, default=fields.Datetime.now)

    @api.onchange('create_by')
    def _onchange_create_by(self):
        for record in self:
            record.create_date = fields.Datetime.now()

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity == 0:
                raise ValidationError("Quantity must be greater than 0!")
    
    # If inventory label is filled, detect the inventory
    @api.onchange('inventory_label')
    def _onchange_inventory_label(self):
        for record in self:
            if record.inventory_label:
                inventory = self.env['ae.inventory'].search([('inventory_label', '=', record.inventory_label)])
                if inventory:
                    record.inventory = inventory.id
                else:
                    raise ValidationError("Inventory with label %s is not found in the system!" % record.inventory_label)
            
                
    @api.onchange('inventory')
    def _onchange_inventory(self):
        # Fill the inventory_label
        for record in self:
            record.inventory_label = record.inventory.inventory_label