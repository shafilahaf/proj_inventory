from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# res.users inherited
class ResUsersInherited(models.Model):
    _inherit = 'res.users'

    # Users create limit
    @api.model
    def create(self, vals):
        if self.env.user.has_group('base.group_system'):
            if self.env['res.users'].search_count([]) >= 40:
                raise UserError(_("You can't create more than 40 users. Please contact your administrator."))
        return super(ResUsersInherited, self).create(vals)

# class ResUsersInherited(models.Model):
#     _inherit = 'res.users'

#     last_login = fields.Datetime(string='Last Login')
#     last_logout = fields.Datetime(string='Last Logout')