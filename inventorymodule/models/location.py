from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ae_location(models.Model):
    _name = 'ae.location'
    _description = 'Location'
    _rec_name = 'location_code'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'location_name asc'

    active = fields.Boolean(default=True)
    location_code = fields.Char(string='Location Code', required=True)
    location_name = fields.Char(string='Location Name', required=True)
    location_type = fields.Selection([('1', 'Storage'), ('2', 'Disposal Storage'), ('3', 'Auction Storage'), ('4', 'Loan'), ('5', 'Stationery and Supplies Storage')], string='Location Type', default='4')
    asset_location_code = fields.Char(string='Asset Location Code')
    location_details_id = fields.One2many('ae.location.details', 'location_id', string='Location Lines')
    disposal_storage = fields.Boolean(string='Disposal Storage')
    has_loan_location = fields.Boolean(string='is Loan Location', default=False)
    is_main_storage = fields.Boolean(string='Main Storage', default=False)

    # @api.model
    # def create(self, vals):
    #     if 'location_details_id' not in vals:
    #         raise UserError(_('Cannot create Location without Room Code and Sub Room Code. Please add Room Code and Sub Room Code first.'))
    #     return super(ae_location, self).create(vals)

    @api.model
    def create(self, vals):
        res = super(ae_location, self).create(vals)

        action_description = f"Location {res.location_name} has been created."

        self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Location')

        # if 'location_details_id' not in vals:
        #     raise UserError(_('Cannot create Location without Room Code and Sub Room Code. Please add Room Code and Sub Room Code first.'))
        
        return res
    
    def write(self, vals):
        # res = super(ae_location, self).write(vals)

        # updated_fields = []
        # for field in self._fields:
        #     if field in vals:
        #         updated_fields.append(field)
        # action_description = f"Location {self.location_name} has been updated. Updated fields: {', '.join(updated_fields)}"
        # self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Location')

        # return res
        updated_fields = []
        for record in self:
            for field in self._fields:
                if field in vals:
                    updated_fields.append(field)
            action_description = f"Location {record.location_name} has been updated. Updated fields: {', '.join(updated_fields)}"
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Location')
        return super(ae_location, self).write(vals)
    
    def unlink(self):
        for rec in self:
            action_description = f"Location {rec.location_name} has been deleted."
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Location')
        return super(ae_location, self).unlink()

class ae_location_details(models.Model):
    _name = 'ae.location.details'
    _description = 'Location Details'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    location_id = fields.Many2one('ae.location', string='Location', ondelete='cascade', readonly=True)
    room_code = fields.Many2one('ae.master.room', string='Room Code', required=True)
    sub_room_code = fields.Many2many('ae.master.sub.room', string='Sub Room Code', required=True)