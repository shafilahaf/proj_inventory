from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ae_master_vendor(models.Model):
    _name = 'ae.master.vendor'
    _description = 'Master Vendor'
    _rec_name = 'vendor_name'
    _order = 'vendor_name asc'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    vendor_code = fields.Char(string='Vendor Code', required=True)
    vendor_name = fields.Char(string='Vendor Name', required=True)
    vendor_address = fields.Text(string='Address', required=True)
    vendor_contactperson= fields.Char(string='Contact Person', required=True)
    vendor_contactno= fields.Char(string='Contact Number', required=True)
    vendor_email= fields.Char(string='Email', required=True)

    # Uppercase vendor code
    @api.onchange('vendor_code')
    def _onchange_vendor_code(self):
        if self.vendor_code:
            self.vendor_code = self.vendor_code.upper().replace(" ", "")

    # Uppercase vendor name
    @api.onchange('vendor_name')
    def _onchange_vendor_name(self):
        if self.vendor_name:
            self.vendor_name = self.vendor_name.upper()

    @api.constrains('vendor_code')
    def _check_vendor_code(self):
        for rec in self:
            if rec.vendor_code:
                if rec.search([('vendor_code', '=', rec.vendor_code), ('id', '!=', rec.id)]):
                    raise ValidationError(_('Vendor Code must be unique!'))
                
    @api.constrains('vendor_name')
    def _check_vendor_name(self):
        for rec in self:
            if rec.vendor_name:
                if rec.search([('vendor_name', '=', rec.vendor_name), ('id', '!=', rec.id)]):
                    raise ValidationError(_('Vendor Name must be unique!'))

    @api.model
    def create(self, vals):
        res = super(ae_master_vendor, self).create(vals)

        action_description = f"Vendor {res.vendor_name} has been created."

        self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Vendor')

        return res
    
    def write(self, vals):
        # res = super(ae_master_vendor, self).write(vals)

        # updated_fields = []
        # for field in self._fields:
        #     if field in vals:
        #         updated_fields.append(field)
        # action_description = f"Vendor {self.vendor_name} has been updated. Updated fields: {', '.join(updated_fields)}"
        # self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Vendor')

        # return res
        updated_fields = []
        for record in self:
            for field in record._fields:
                if field in vals:
                    updated_fields.append(field)
            action_description = f"Vendor {record.vendor_name} has been updated. Updated fields: {', '.join(updated_fields)}"
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Vendor')
        return super(ae_master_vendor, self).write(vals)
    
    def unlink(self):
        for rec in self:
            action_description = f"Vendor {rec.vendor_name} has been deleted."
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Vendor')
        return super(ae_master_vendor, self).unlink()