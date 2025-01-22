from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class ae_user_logs(models.Model):
    _name = 'ae.user.logs'
    _description = 'User Logs'
    _order = 'action_date desc'

    user_id = fields.Many2one('res.users', string='User')
    action_date = fields.Datetime(string='Action Date')
    action_description = fields.Char(string='Action Description')
    module = fields.Char(string='Module')

    @api.model
    def create_user_log(self, user_id, action_description, module):
        log = self.create({
            'user_id': user_id,
            'action_date': fields.Datetime.now(),
            'action_description': action_description,
            'module': module
        })

        return log

class ae_login_logout_log(models.Model):
    _name = 'ae.login.logout.log'
    _description = 'Login Logout Log'
    _order = 'login_date desc'

    user_id = fields.Many2one('res.users', string='User')
    login_date = fields.Datetime(string='Login Date')
    logout_date = fields.Datetime(string='Logout Date')