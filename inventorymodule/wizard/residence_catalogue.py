from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import json

class ResidenceCatalogue(models.TransientModel):
    _name = 'ae.residence.catalogue'
    _description = 'Residence Catalogue'

    ae_location = fields.Many2one('ae.location', string='Location Code', required=True)
    ae_location_name = fields.Char(string='Location Name')
    printed_date = fields.Date(string='Printed Date', default=fields.Date.today, store=True)
    printed_date_char = fields.Char(string='Printed Date Char', compute='_compute_printed_date_char')
    group_type = fields.Char(string='Group Type', default='Furniture')

    @api.depends('printed_date')
    def _compute_printed_date_char(self):
        """
        Compute Printed Date Char from Printed Date"""
        for rec in self:
            rec.printed_date_char = rec.printed_date.strftime('%d %B %Y')

    @api.onchange('ae_location')
    def onchange_ae_location(self):
        """
        Set Location Name based on Location Code"""
        if self.ae_location:
            self.ae_location_name = self.ae_location.location_name
            
    # def action_print_report(self):
    #     """
    #     Print Residence Catalogue Report"""
    #     domain = []
        
    #     if self.ae_location:
    #         domain.append(('inventory_location_code', '=', self.ae_location.id))

    #     domain.append(('inventory_type', 'in', [1,2]))
        
    #     inventories = self.env['ae.inventory'].search(domain)
    #     sorted_inventories = sorted(inventories, key=lambda r: (r.inventory_group.group_type or ''))

    #     unique_inventories = defaultdict(lambda: {'subrooms': defaultdict(int), 'details': None})
        
    #     for inventory in sorted_inventories:
    #         name = inventory.inventory_name
    #         if name not in unique_inventories:
    #             picture = inventory.inventory_picture if inventory.inventory_picture else False
    #             picture_url = '/web/image/ae.inventory/' + str(inventory.id) + '/inventory_picture' if inventory.inventory_picture else False
    #             vals = {
    #                 'index' : len(unique_inventories) + 1,
    #                 'name': name,
    #                 'id': inventory.id,
    #                 'width': inventory.inventory_width,
    #                 'height': inventory.inventory_height,
    #                 'length': inventory.inventory_length,
    #                 'picture': picture_url,
    #                 'type': inventory.inventory_group.group_type,
    #                 'total_stock': self.env['ae.inventory'].search_count([('inventory_name', '=', name), ('inventory_location_code', '=', self.ae_location.id)]),
    #             }
    #             unique_inventories[name]['details'] = vals

    #         # unique_inventories[name]['subrooms'][inventory.inventory_sub_room_code.sub_room_name] += 1
    #         room_name = inventory.inventory_room_code.room_name
    #         unique_inventories[name]['subrooms'][f"{room_name} - {inventory.inventory_sub_room_code.sub_room_name}"] += 1

    #     inv_list = []
    #     for name, info in unique_inventories.items():
    #         details = info['details']
    #         # details['subroom'] = [f"{subroom} = {count}" for subroom, count in info['subrooms'].items()]
    #         details['subroom'] = [f"{subroom} = {count}" for subroom, count in info['subrooms'].items()]
    #         inv_list.append(details)

    #     data = {
    #         'form_data' : self.read()[0],
    #         'inventories' : inv_list,
    #     }

    #     # See data in json format
    #     # raise ValidationError(json.dumps(data, indent=4))

    #     return self.env.ref('inventorymodule.action_report_residence_catalogue').report_action(self, data=data)

    def action_print_report(self):
        # Initialize the domain
        domain = []

        if self.ae_location:
            domain.append(('inventory_location_code', '=', self.ae_location.id))
        
        domain.append(('inventory_type', 'in', [1, 2]))

        inventories = self.env['ae.inventory'].search(domain)
        
        # Filter sorted inventories by group type, ignoring case and spaces
        if self.group_type:
            normalized_group_type = ''.join(self.group_type.split()).lower()
            inventories = inventories.filtered(lambda r: ''.join((r.inventory_group.group_type or '').split()).lower() == normalized_group_type)
        
        # Sort the inventories
        sorted_inventories = sorted(inventories, key=lambda r: (r.inventory_group.group_type or ''))

        # Unique inventories dictionary to store data
        unique_inventories = defaultdict(lambda: {'subrooms': defaultdict(int), 'details': None})
        
        for inventory in sorted_inventories:
            name = inventory.inventory_name
            if name not in unique_inventories:
                picture = inventory.inventory_picture if inventory.inventory_picture else False
                picture_url = '/web/image/ae.inventory/' + str(inventory.id) + '/inventory_picture' if inventory.inventory_picture else False

                vals = {
                    'index': len(unique_inventories) + 1,
                    'name': name,
                    'width': inventory.inventory_width,
                    'height': inventory.inventory_height,
                    'length': inventory.inventory_length,
                    'picture': picture_url,
                    'type': inventory.inventory_group.group_type,
                    'total_stock': self.env['ae.inventory'].search_count([('inventory_name', '=', name), ('inventory_location_code', '=', self.ae_location.id)]),
                }
                unique_inventories[name]['details'] = vals

            room_name = inventory.inventory_room_code.room_name
            unique_inventories[name]['subrooms'][f"{room_name} - {inventory.inventory_sub_room_code.sub_room_name}"] += 1

        inv_list = []
        for name, info in unique_inventories.items():
            details = info['details']
            details['subroom'] = [f"{subroom} = {count}" for subroom, count in info['subrooms'].items()]
            inv_list.append(details)

        data = {
            'form_data': self.read()[0],
            'inventories': inv_list,
        }

        return self.env.ref('inventorymodule.action_report_residence_catalogue').report_action(self, data=data)