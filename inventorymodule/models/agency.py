from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ae_master_agency(models.Model):
    _name = 'ae.master.agency'
    _description = 'Master Agency'
    _rec_name = 'agency_name'
    _order = 'agency_name asc'

    active = fields.Boolean(default=True)
    agency_code = fields.Char(string='Agency No.', required=True)
    agency_name = fields.Char(string='Agency Name', required=True)
    gl_code = fields.Char(string='GL Code', required=True)
    assignment = fields.Char(string='Assignment', required=True)
    fmis_code = fields.Char(string='FMIS Code')
    description = fields.Text(string='Description')
    is_non_dfat = fields.Boolean(string='Non DFAT', default=False, help='Check if the document is non DFAT')

    # Uppercase agency code
    @api.onchange('agency_code')
    def _onchange_agency_code(self):
        if self.agency_code:
            self.agency_code = self.agency_code.upper().replace(" ", "")

    # Uppercase agency name
    @api.onchange('agency_name')
    def _onchange_agency_name(self):
        if self.agency_name:
            self.agency_name = self.agency_name.upper()

    # agency_code must be unique
    @api.constrains('agency_code')
    def _check_agency_code(self):
        for record in self:
            if record.agency_code:
                agency_code = self.env['ae.master.agency'].search([('agency_code', '=', record.agency_code)])
                if len(agency_code) > 1:
                    raise ValidationError("Agency Code must be unique!")
                
    # gl_code must be unique
    # @api.constrains('gl_code')
    # def _check_gl_code(self):
    #     for record in self:
    #         if record.gl_code:
    #             gl_code = self.env['ae.master.agency'].search([('gl_code', '=', record.gl_code)])
    #             if len(gl_code) > 1:
    #                 raise ValidationError("GL Code must be unique!")
                
    @api.model
    def create(self, vals):
        res = super(ae_master_agency, self).create(vals)

        action_description = f"Agency {res.agency_name} has been created."

        self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Agency')

        return res
    
    def write(self, vals):
        # res = super(ae_master_agency, self).write(vals)

        # updated_fields = []
        # for field in self._fields:
        #     if field in vals:
        #         updated_fields.append(field)
        # action_description = f"Agency {self.agency_name} has been updated. Updated fields: {', '.join(updated_fields)}"
        # self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Agency')

        # return res
        updated_fields = []
        for record in self:
            for field in record._fields:
                if field in vals:
                    updated_fields.append(field)
            action_description = f"Agency {record.agency_name} has been updated. Updated fields: {', '.join(updated_fields)}"
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Agency')
        return super(ae_master_agency, self).write(vals)
    
    def unlink(self):
        for rec in self:
            action_description = f"Agency {rec.agency_name} has been deleted."
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Agency')
        return super(ae_master_agency, self).unlink()