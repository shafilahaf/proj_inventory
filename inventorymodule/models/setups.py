from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ae_master_room(models.Model):
    _name = 'ae.master.room'
    _description = 'Master Room'
    _rec_name = 'room_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    active = fields.Boolean(default=True)
    room_code = fields.Char(string='Room Code', required=True)
    room_name = fields.Char(string='Room Name', required=True)
    location_details_ids = fields.Many2many('ae.location.details', string='Location Details', compute='_compute_location_details')

    # Uppercase room code
    @api.onchange('room_code')
    def _onchange_room_code(self):
        if self.room_code:
            self.room_code = self.room_code.upper().replace(" ", "")

    # Uppercase room name
    @api.onchange('room_name')
    def _onchange_room_name(self):
        if self.room_name:
            self.room_name = self.room_name.upper()

    @api.depends('location_details_ids')
    def _compute_location_details(self):
        for room in self:
            room.location_details_ids = self.env['ae.location.details'].search([('room_code', '=', room.id)])

    # Cannot duplicate room code
    @api.constrains('room_code')
    def _check_duplicate_room_code(self):
        for room in self:
            if self.env['ae.master.room'].search_count([('room_code', '=', room.room_code)]) > 1:
                raise ValidationError('Room Code must be unique! It has been used in another Room!')


class ae_master_sub_room(models.Model):
    _name = 'ae.master.sub.room'
    _description = 'Master Sub Room'
    _rec_name = 'sub_room_code'
    _order = 'create_date desc'
    
    active = fields.Boolean(default=True)
    sub_room_code = fields.Char(string='Sub Room Code', required=True)
    sub_room_name = fields.Char(string='Sub Room Name', required=True)

    # Uppercase sub room code
    @api.onchange('sub_room_code')
    def _onchange_sub_room_code(self):
        if self.sub_room_code:
            self.sub_room_code = self.sub_room_code.upper().replace(" ", "")

    # Uppercase sub room name
    @api.onchange('sub_room_name')
    def _onchange_sub_room_name(self):
        if self.sub_room_name:
            self.sub_room_name = self.sub_room_name.upper()
    
    # Cannot duplicate sub room code
    @api.constrains('sub_room_code')
    def _check_duplicate_sub_room_code(self):
        for sub_room in self:
            if self.env['ae.master.sub.room'].search_count([('sub_room_code', '=', sub_room.sub_room_code)]) > 1:
                raise ValidationError('Sub Room Code must be unique! It has been used in another Sub Room!')
