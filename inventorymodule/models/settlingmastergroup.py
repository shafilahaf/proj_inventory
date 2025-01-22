from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class settling_master_group(models.Model):
    _name = 'ae.settling.master.group'
    _description = 'Settling Master Group'
    _rec_name = 'name'
    _order = 'level asc'
    _sql_constraints = [
        ('level_unique', 'unique(level)', 'Level must be unique!'),
        ('name_unique', 'unique(name)', 'Name must be unique!'),
    ]

    level = fields.Integer(string='Level', required=True)
    name = fields.Char(string='Name', required=True)

    # Uppercase name
    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name = self.name.upper()

    @api.model
    def create(self, vals):
        res = super(settling_master_group, self).create(vals)

        action_description = f"Settling Master Group {res.name} has been created."

        self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Settling Master Group')

        return res
    
    def write(self, vals):
        # res = super(settling_master_group, self).write(vals)

        # updated_fields = []
        # for field in self._fields:
        #     if field in vals:
        #         updated_fields.append(field)
        # action_description = f"Settling Master Group {self.name} has been updated. Updated fields: {', '.join(updated_fields)}"
        # self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Settling Master Group')

        # return res

        updated_fields = []
        for record in self:
            for field in self._fields:
                if field in vals:
                    updated_fields.append(field)
            action_description = f"Settling Master Group {record.name} has been updated. Updated fields: {', '.join(updated_fields)}"
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Settling Master Group')
        return super(settling_master_group, self).write(vals)
    
    def unlink(self):
        for rec in self:
            action_description = f"Settling Master Group {rec.name} has been deleted."
            self.env['ae.user.logs'].create_user_log(self.env.user.id, action_description, 'Settling Master Group')
        return super(settling_master_group, self).unlink()