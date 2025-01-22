from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class updateSourcePriceInventory(models.TransientModel):
    _name = 'ae.inventory.update.source.price'

    def updateSourcePriceInventory(self):
        ledger_model = self.env['ae.inventory.ledger.entry']
        inventory_records = self.env['ae.inventory'].search([('inventory_type', '=', '4')])

        for inventory in inventory_records:
            # Search ledger entries related to the current inventory
            ledger_entries = ledger_model.search([
                ('entry_type', '=', '9'),
                ('inventory_name', '=', inventory.inventory_name)
            ])
            
            if ledger_entries:
                # Get the highest source price from the ledger entries
                highest_ledger_price = max(ledger_entries.mapped('source_price'))
                
                # Update the inventory if the highest ledger price is greater than the current highest source price
                if highest_ledger_price > inventory.highest_source_price:
                    inventory.write({'highest_source_price': highest_ledger_price})

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


    def updateSourcePriceInventorySales(self):
        # Get all items in inventory
        items = self.env['ae.inventory'].search([('inventory_type', '=', '4'), ('highest_source_price', '=', 0)])
        for item in items:
            # Get source price in ledger
            ledger = self.env['ae.inventory.ledger.entry'].search([('inventory_name', '=', item.inventory_name), ('entry_type', '=', '10')], order='posting_date desc', limit=1)
            if ledger:
                if ledger.source_price > item.highest_source_price:
                    item.write({'highest_source_price': ledger.source_price})
            else:
                pass

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def updateSourcePriceInventoryPurchaseSourcePrice(self):
        items = self.env['ae.inventory'].search([('inventory_type', '=', '4'), ('purchase_uom', '!=', False)])

        # Update Source Price in Inventory from Purchase Source Price
        for item in items:
            # Get source price in ledger
            ledger = self.env['ae.inventory.ledger.entry'].search([('inventory_name', '=', item.inventory_name), ('entry_type', '=', '9')], order='posting_date desc', limit=1)
            if ledger:
                item.write({'highest_source_price': ledger.source_price_purchase})
            else:
                pass

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }