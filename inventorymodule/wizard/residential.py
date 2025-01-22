from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class residential_reports_wizard(models.TransientModel):
    _name = 'ae.residential.reports.wizard'
    _description = 'Residential Reports Wizard'

    ae_location = fields.Many2one('ae.location', string='Location Code', required=True)
    ae_location_name = fields.Char(string='Location Name')
    ae_asset_number = fields.Char(string='Asset Number')
    ae_asset_numbers = fields.Char(string='Asset Number')
    printed_date = fields.Date(string='Printed Date', default=fields.Date.today, store=True)
    printed_date_char = fields.Char(string='Printed Date Char', compute='_compute_printed_date_char')

    @api.depends('printed_date')
    def _compute_printed_date_char(self):
        for rec in self:
            rec.printed_date_char = rec.printed_date.strftime('%d %B %Y')

    @api.onchange('ae_location')
    def onchange_ae_location(self):
        # self.ae_location_name = self.ae_location.location_name
        if self.ae_location:
            self.ae_location_name = self.ae_location.location_name
            self.ae_asset_numbers = self.ae_location.asset_location_code

    def action_print_report(self):
        domain = []
        
        if self.ae_location:
            domain.append(('inventory_location_code', '=', self.ae_location.id))
        if self.ae_asset_number:
            domain.append(('inventory_location_code.asset_location_code', '=', self.ae_asset_number))
        
        # inventories = self.env['ae.inventory'].search(domain, order='inventory_room_name,inventory_room_subroom_name,inventory_label asc')

        inventories = self.env['ae.inventory'].search(domain)
        sorted_inventories = inventories.sorted(key=lambda r: (r.inventory_location_code.location_code or '', r.inventory_room_code.room_name or '', r.inventory_sub_room_code.sub_room_name or '', r.inventory_label or ''))

        inv_list = []
        prev_apartno = False
        prev_roomarea = False
        prev_roomname = False
        prev_roomcode = False
        for index, inventory in enumerate(sorted_inventories):
            domain2 = []
            domain2.append(('inventory_remarks', '=', inventory.inventory_remarks))

            inventories2 = self.env['ae.inventory'].search(domain2)

            # Get remarks
            # remarks = inventory.inventory_remarks if inventory.inventory_remarks else '-'

            vals = {
                'index' : index + 1,
                'apartement_no' : inventory.inventory_location_code.location_code if inventory.inventory_location_code.location_code != prev_apartno else '',
                'room_area' : inventory.inventory_room_code.room_name if inventory.inventory_room_code.room_name != prev_roomarea else '',
                'room_name' : inventory.inventory_sub_room_code.sub_room_name if inventory.inventory_sub_room_code.sub_room_name != prev_roomname else '',
                'room_code' : inventory.inventory_sub_room_code.sub_room_code if inventory.inventory_sub_room_code.sub_room_code != prev_roomcode else '',
                'reftag' : inventory.inventory_group.name,
                'name': inventory.inventory_name,
                'code': inventory.inventory_code,
                'inventorylabel': inventory.inventory_label,
                'remarks': inventory.inventory_remarks,
                'assetno': inventory.inventory_location_code.asset_location_code,
                'reccount' : len(inventories2) if len(inventories2) > 1 else '',
            }
            inv_list.append(vals)
            prev_apartno = inventory.inventory_location_code.location_code
            prev_roomarea = inventory.inventory_room_code.room_name
            prev_roomname = inventory.inventory_sub_room_code.sub_room_name
            prev_roomcode = inventory.inventory_sub_room_code.sub_room_code

        data = {
            'form_data' : self.read()[0],
            'inventories' : inv_list,
        }
        return self.env.ref('inventorymodule.action_report_residential').report_action(self, data=data)