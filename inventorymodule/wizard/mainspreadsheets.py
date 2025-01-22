from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class main_spreadsheets_reports_wizard(models.TransientModel):
    _name = 'ae.inventory.main.spreadsheets.reports.wizard'
    _description = 'Main Spreadsheets Reports Wizard'

    ae_location = fields.Many2one('ae.location', string='Location Code')
    ae_asset_number = fields.Char(string='Asset Number')
    ae_inventory_group = fields.Many2one('ae.inventory.master.group', string='Inventory Group')
    print_date = fields.Date(string='Date', default=fields.Date.today, required=True)
    print_date_char = fields.Char(string='Date', compute='_compute_print_date_char', store=True)

    @api.depends('print_date')
    def _compute_print_date_char(self):
        for rec in self:
            rec.print_date_char = rec.print_date.strftime('%d %B %Y')

    def action_print_report(self):
        domain = []
        
        if self.ae_location:
            domain.append(('inventory_location_code', '=', self.ae_location.id))

        if self.ae_asset_number:
            domain.append(('inventory_asset_number', '=', self.ae_asset_number))
            
        if self.ae_inventory_group:
            domain.append(('inventory_group', '=', self.ae_inventory_group.id))

        # Add filter for inventory_type
        domain.append(('inventory_type', 'in', [1,2]))
        
        inventories = self.env['ae.inventory'].search(domain)
        sorted_inventories = sorted(inventories, key=lambda inv: inv.inventory_label)

        inv_list = []
        for index, inventory in enumerate(sorted_inventories):
            vals = {
                'index' : index + 1,
                'reftag' : inventory.inventory_group.name,
                'name': inventory.inventory_name,
                'label': inventory.inventory_label,
                'asset_number': inventory.inventory_asset_number,
                'locationcode': inventory.inventory_location_code.location_name,
                'roomcode': inventory.inventory_room_code.room_name,
                'subroomcode': inventory.inventory_sub_room_code.sub_room_name,
            }
            inv_list.append(vals)

        data = {
            'form_data' : self.read()[0],
            'inventories' : inv_list,
        }
        return self.env.ref('inventorymodule.action_report_mainspreadsheet').report_action(self, data=data)