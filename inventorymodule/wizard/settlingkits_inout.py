from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from itertools import groupby

# Not Used
class settlingkits_inout_reports_wizard(models.TransientModel):
    _name = 'ae.inventory.settlingkits.inout.reports.wizard'
    _description = 'Settling Kits In/Out Reports Wizard'

    settlingkit_document_no = fields.Many2one('ae.settlingkit.header', string='Document No.')
    settlingkit_posting_date = fields.Date(string='Date')
    tenant_name = fields.Char(string='Tenant Name', size=100)
    tenant_address = fields.Char(string='Tenant Address', size=100)
    delivery_date = fields.Date(string='Delivery Date')
    returned_date = fields.Date(string='Returned Date')

    @api.onchange('settlingkit_document_no')
    def _onchange_settlingkit_document_no(self):
        for rec in self:
            if rec.settlingkit_document_no:
                rec.tenant_name = rec.settlingkit_document_no.tenant_name
                rec.tenant_address = rec.settlingkit_document_no.z
                rec.delivery_date = rec.settlingkit_document_no.delivery_date
                rec.returned_date = rec.settlingkit_document_no.returned_date


    def action_print_report(self):
        domain_line = []
        if self.settlingkit_document_no:
            domain_line.append(('settling_kit_header_id', '=', self.settlingkit_document_no.id))
        if self.settlingkit_posting_date:
            domain_line.append(('settling_kit_header_id.posting_date', '=', self.settlingkit_posting_date))

        settling_kit_line = self.env['ae.settlingkit.line'].search(domain_line)
        
        if not settling_kit_line:
            raise UserError('No record(s) found!')

        # Line
        setkit_list_line = []
        for index, setkit in enumerate(settling_kit_line):
            vals = {
                'index' : index + 1,
                'description': setkit.inventory.inventory_name,
                'out_quantity': setkit.quantity,
                'return_quantity': setkit.return_quantity,
                'notes': setkit.notes if setkit.notes else '',
            }
            setkit_list_line.append(vals)

        data = {
            'form_data' : self.read()[0],
            'settling_kit_line' : setkit_list_line,
        }
        return self.env.ref('inventorymodule.action_report_settlingkitsinout').report_action(self, data=data)