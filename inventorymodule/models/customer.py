from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import base64


class ae_master_customer(models.Model):
    _name = 'ae.master.customer'
    _description = 'Master Customer'
    _rec_name = 'customer_name'
    _order = 'customer_name asc'

    active = fields.Boolean(default=True)
    customer_code = fields.Char(string='Customer No.', required=True)
    customer_name = fields.Char(string='Customer Name', required=True)

    # Uppercase customer code
    @api.onchange('customer_code')
    def _onchange_customer_code(self):
        if self.customer_code:
            self.customer_code = self.customer_code.upper().replace(" ", "")

    # Uppercase customer name
    @api.onchange('customer_name')
    def _onchange_customer_name(self):
        if self.customer_name:
            self.customer_name = self.customer_name.upper()
    

    @api.constrains('customer_code')
    def _check_customer_code(self):
        for rec in self:
            if rec.customer_code:
                if rec.search([('customer_code', '=', rec.customer_code), ('id', '!=', rec.id)]):
                    raise ValidationError(_('Customer Code must be unique!'))
                
    @api.constrains('customer_name')
    def _check_customer_name(self):
        for rec in self:
            if rec.customer_name:
                if rec.search([('customer_name', '=', rec.customer_name), ('id', '!=', rec.id)]):
                    raise ValidationError(_('Customer Name must be unique!'))

    @api.model
    def create(self, vals):
        res = super(ae_master_customer, self).create(vals)

        action_description = f"Customer {res.customer_name} has been created."

        self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Customer')

        return res
    
    def write(self, vals):
        # res = super(ae_master_customer, self).write(vals)

        # updated_fields = []
        # for field in self._fields:
        #     if field in vals:
        #         updated_fields.append(field)
        # action_description = f"Customer {self.customer_name} has been updated. Updated fields: {', '.join(updated_fields)}"
        # self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Customer')

        # return res
        updated_fields = []
        for record in self:
            for field in record._fields:
                if field in vals:
                    updated_fields.append(field)
            action_description = f"Customer {record.customer_name} has been updated. Updated fields: {', '.join(updated_fields)}"
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Customer')
        return super(ae_master_customer, self).write(vals)
    
    def unlink(self):
        for rec in self:
            action_description = f"Customer {rec.customer_name} has been deleted."
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Customer')
        return super(ae_master_customer, self).unlink()

