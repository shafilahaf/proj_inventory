from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)

class storage_management_reports_wizard(models.TransientModel):
    _name = 'ae.storage.management.reports.wizard'
    _description = 'Storage Management Reports Wizard'

    ae_location = fields.Many2one('ae.location', string='Location Code')
    ae_inventory_group = fields.Many2one('ae.inventory.master.group', string='Inventory Group')
    print_date = fields.Date(string='Date', default=fields.Date.today, required=True)
    ae_location_name = fields.Char(string='Location Name', related='ae_location.location_name', readonly=True)
    print_date_char = fields.Char(string='Date', compute='_compute_print_date_char', readonly=True)

    inventory_room_code = fields.Many2one('ae.master.room', string='Room Code', domain="[('id', 'in', available_rooms)]")
    inventory_sub_room_code = fields.Many2one('ae.master.sub.room', string='Sub Room Code', domain="[('id', 'in', available_sub_rooms)]")
    available_rooms = fields.Many2many('ae.master.room', compute='_compute_available_rooms')
    available_sub_rooms = fields.Many2many('ae.master.sub.room', compute='_compute_available_sub_rooms')

    inventory_room_code_name = fields.Char(string='Room Name', related='inventory_room_code.room_code', readonly=True)
    inventory_sub_room_code_name = fields.Char(string='Sub Room Name', related='inventory_sub_room_code.sub_room_code', readonly=True)

    @api.depends('ae_location')
    def _compute_available_rooms(self):
        """
        Get available rooms from location_details_id."""
        for record in self:
            record.available_rooms = record.ae_location.location_details_id.mapped('room_code')

    @api.depends('inventory_room_code')
    def _compute_available_sub_rooms(self):
        """
        Get available sub rooms from location_details_id."""
        # for record in self:
        #     record.available_sub_rooms = record.inventory_room_code.location_details_ids.mapped('sub_room_code')
        for record in self:
            record.available_sub_rooms = record.ae_location.location_details_id.filtered(lambda r: r.room_code.id == record.inventory_room_code.id).mapped('sub_room_code')

    @api.depends('print_date')
    def _compute_print_date_char(self):
        for rec in self:
            rec.print_date_char = rec.print_date.strftime('%d %B %Y')

    def action_print_report2(self):
        try:
            domain = []
    
            if self.ae_inventory_group:
                domain.append(('inventory_group', '=', self.ae_inventory_group.id))

            if self.ae_location:
                domain.append(('inventory_location_code', '=', self.ae_location.id))

            # Room
            if self.inventory_room_code:
                domain.append(('inventory_room_code', '=', self.inventory_room_code.id))

            # Sub Room
            if self.inventory_sub_room_code:
                domain.append(('inventory_sub_room_code', '=', self.inventory_sub_room_code.id))

            # Add filter for inventory_type
            domain.append(('inventory_type', 'in', [1, 2]))
            
            inventories = self.env['ae.inventory'].search(domain) #24/11/2023 - inventory_group_level asc -> inventory_label asc
            sorted_inventories = inventories.sorted(key=lambda r: (r.inventory_label or '', r.inventory_group_level))

            inventory_groups = defaultdict(lambda: defaultdict(list))

            for inventory in sorted_inventories:
                reftag = inventory.inventory_group.name if inventory.inventory_group.name else False
                picture = inventory.inventory_group.picture if inventory.inventory_group.picture else False
                picture_url = '/web/image/ae.inventory.group/' + str(inventory.inventory_group.id) + '/picture' if inventory.inventory_group.picture else False
                # picture = False
                inventory_groups[reftag][picture].append({
                    'index': len(inventory_groups[reftag][picture]) + 1,
                    'reftag': reftag,
                    'name': inventory.inventory_name,
                    'label': inventory.inventory_label,
                    'remarks': inventory.inventory_remarks,
                    # 'picture': picture,
                    'picture': picture_url,
                })

            inv_list = []

            for reftag, picture_data in inventory_groups.items():
                for picture, group_data in picture_data.items():
                    inv_list.append({
                        'reftag': reftag,
                        'picture': picture,
                        'inventory_group_data': group_data,
                    })

            data = {
                'form_data': self.read()[0],
                'inventory_groups': inv_list,
            }
            return self.env.ref('inventorymodule.action_report_storagemanagementdua').report_action(self, data=data)
        except Exception as e:
            _logger.error(e)
            raise UserError(e)

