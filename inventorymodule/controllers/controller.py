from odoo import http

from odoo.addons.web.controllers.main import Home, Session
from odoo.http import request
from odoo.fields import Datetime

# When user login create to model ae.login.logout.log for audit login and logout user
# class HomeInherit(Home):
#     @http.route()

#     def web_login(self, redirect=None, **kw):
#         res = super(HomeInherit, self).web_login(redirect=None, **kw)
#         if request.params['login_success']:
#             user = request.env['res.users'].sudo().search([('login', '=', kw['login'])], limit=1)
#             if user:
#                 ICPSudo = request.env['ir.config_parameter'].sudo()
#                 need_to_store = ICPSudo.get_param('user_login_status.store_user_time')
#                 if need_to_store:
#                     request.env['ae.login.logout.log'].sudo().create({
#                         'user_id': user.id,
#                         'login_date': Datetime.now(),
#                     })
#         return res

# ###############
class HomeInherit(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        res = super(HomeInherit, self).web_login(redirect=None, **kw)
        if request.params['login_success']:
            user = request.env['res.users'].sudo().search([('login', '=', kw['login'])], limit=1)
            if user:
                ICPSudo = request.env['ir.config_parameter'].sudo()
                need_to_store = ICPSudo.get_param('user_login_status.store_user_time')
                if need_to_store:
                    log_model = request.env['ae.login.logout.log'].sudo()
                    record = log_model.search(
                        [('user_id', '=', user.id), ('logout_date', '=', False)], limit=1)

                    if record:
                        # If a record exists, update the login date
                        record.login_date = Datetime.now()
                    else:
                        # If no record exists, create a new one
                        log_model.create({
                            'user_id': user.id,
                            'login_date': Datetime.now(),
                        })
        return res
# ###############
    
# When user logout update logout_date in model ae.login.logout.log
class SessionInherit(Session):
    @http.route()
    def logout(self, redirect='/web'):
        user = request.env['res.users'].sudo().search([('id', '=', request.session.uid)], limit=1)
        if user:
            ICPSudo = request.env['ir.config_parameter'].sudo()
            need_to_store = ICPSudo.get_param('user_login_status.store_user_time')
            if need_to_store:
                record = request.env['ae.login.logout.log'].sudo().search(
                    [('user_id', '=', user.id), ('logout_date', '=', False)], limit=1)
                if record:
                    record.logout_date = Datetime.now()
        return super(SessionInherit, self).logout(redirect=redirect)
    
