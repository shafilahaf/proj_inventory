from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import base64
from collections import defaultdict


class stationary_issued_wizard(models.TransientModel):
    _name = 'ae.inventory.stationary.issued.wizard'
    _description = 'Stationary Issued Wizard'

    entry_type = fields.Selection([('10', 'Sales')], string='Entry Type', required=True, default='10')
    # document_no = fields.Many2one('ae.inventory.ledger.entry', string='Document No.', required=True, domain="[('entry_type', '=', entry_type)]")
    # vendor_name = fields.Many2one('ae.master.vendor', string='Vendor Name', required=True)
    customer_name = fields.Many2one('ae.master.customer', string='Customer Name')
    starting_date = fields.Date(string='Starting Date', required=True)
    ending_date = fields.Date(string='Ending Date', required=True)
    get_month_year = fields.Char(string='Month/Year', compute='_compute_month_year', store=True)
    isgetallcustomer = fields.Boolean(string='Get All Customer', default=False)
    starting_date_char = fields.Char(string='Starting Date Char', compute='_compute_starting_date_char', store=True)
    ending_date_char = fields.Char(string='Ending Date Char', compute='_compute_ending_date_char', store=True)

    @api.constrains('starting_date', 'ending_date')
    def _check_date(self):
        for rec in self:
            if rec.starting_date > rec.ending_date:
                raise ValidationError('Starting Date cannot be greater than Ending Date.')
            
    @api.depends('starting_date')
    def _compute_starting_date_char(self):
        for rec in self:
            if rec.starting_date:
                rec.starting_date_char = rec.starting_date.strftime("%d %B %Y")

    @api.depends('ending_date')
    def _compute_ending_date_char(self):
        for rec in self:
            if rec.ending_date:
                rec.ending_date_char = rec.ending_date.strftime("%d %B %Y")

    def action_print_report(self):
        # inv_led_entry = self.env['ae.inventory.ledger.entry'].search([('entry_type', '=', self.entry_type), ('source_name', '=', self.customer_name.customer_name), ('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date), ('isStationeryIssued', '=', False)])
        # item_journal_sales = self.env['ae.itemjournal.header'].search([('customer_name', '=', self.customer_name.customer_name), ('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date)])

        # Get all customer in inventory ledger entry if isgetallcustomer is True
        if self.isgetallcustomer:
            inv_led_entry = self.env['ae.inventory.ledger.entry'].search([('entry_type', '=', [10,11]), ('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date), ('isStationeryIssued', '=', False)]) #order='posting_date, inventory_name, source_name ASC'
            # Sort inventory ledger entry by posting date, inventory name
            inv_led_entry = inv_led_entry.sorted(key=lambda r: (r.posting_date, (r.inventory_name or '').strip(), (r.source_name or '').strip()))
            item_journal_sales = self.env['ae.itemjournal.header'].search([('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date)])
        else:
            inv_led_entry = self.env['ae.inventory.ledger.entry'].search([('entry_type', 'in', [10,11]), ('source_name', 'in', [self.customer_name.customer_name, False]), ('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date), ('isStationeryIssued', '=', False)]) #, order='posting_date, inventory_name, source_name ASC'
            # Sort inventory ledger entry by posting date, inventory name
            inv_led_entry = inv_led_entry.sorted(key=lambda r: (r.posting_date, (r.inventory_name or '').strip(), (r.source_name or '').strip()))
            item_journal_sales = self.env['ae.itemjournal.header'].search([('customer_name', '=', self.customer_name.customer_name), ('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date)])
        
        if not inv_led_entry:
            raise UserError('No data found with the given criteria or stationery already issued.')

        stationaery_list = []
        prev_postingdate = False
        # prev_documentNo = False
        sum_total_price = 0

        for index, inv_led in enumerate(inv_led_entry):
            total_price = (-1*inv_led.quantity) * inv_led.source_price
            sum_total_price += total_price

            vals = {
                'index' : index + 1,
                'postingdate': inv_led.posting_date.strftime("%d-%B-%Y") if inv_led.posting_date != prev_postingdate else '',
                'description': inv_led.inventory_name,
                'quantity': inv_led.quantity * -1,
                # 'quantity': inv_led.quantity,
                'unit': inv_led.unit_of_measure,
                'price': "{:,.2f}".format(inv_led.source_price),
                'totalprice': "{:,.2f}".format((inv_led.quantity * -1) * inv_led.source_price),
                'sumtotalprice': "{:,.2f}".format(sum_total_price),
                'customername': inv_led.source_name,
                # 'documentno': inv_led.document_no if inv_led.document_no != prev_documentNo else '',
            }
            stationaery_list.append(vals)
            prev_postingdate = inv_led.posting_date
            # prev_documentNo = inv_led.document_no

        # Update the inventory ledger entry with isStationeryIssued to True
        inv_led_entry.write({'isStationeryIssued': True})

        # Update the item journal header with isStationeryIssued to True and Stationery Issued Document
        item_journal_sales.write({'isStationeryIssued': True, 'stationery_document_no': 'Stationery Issued Document' + ' ' + self.customer_name.customer_name if not self.isgetallcustomer else 'Stationery Issued Document'})

        data = {
            'form_data' : self.read()[0],
            'inv_led_entry' : stationaery_list,
        }

        pdf = self.env.ref('inventorymodule.action_report_stationaryissued')._render_qweb_pdf(self.ids[0], data=data)[0]

        # Create the stationary issued list
        self.env['ae.stationery.issued.list'].create({
            'stationery_issued_document': 'Stationery Issued Document' + ' ' + self.customer_name.customer_name if not self.isgetallcustomer else 'Stationery Issued Document - All Customer',
            'stationery_issued_date': fields.Datetime.now(),
            'get_data_starting_date': self.starting_date,
            'get_data_ending_date': self.ending_date,
            'stationery_printout': base64.b64encode(pdf),
        })

        return self.env.ref('inventorymodule.action_report_stationaryissued').report_action(self, data=data)
    
    # temporary
    def action_print_report2(self):
        if self.isgetallcustomer:
            inv_led_entry = self.env['ae.inventory.ledger.entry'].search([('entry_type', '=', [10]), ('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date), ('isStationeryIssued', '=', False)], order='posting_date ASC')
            item_journal_sales = self.env['ae.itemjournal.header'].search([('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date)])
            customer_name = []
            for rec in inv_led_entry:
                if rec.source_name not in customer_name:
                    customer_name.append(rec.source_name)
        else:
            inv_led_entry = self.env['ae.inventory.ledger.entry'].search([('entry_type', 'in', [10]), ('source_name', 'in', [self.customer_name.customer_name, False]), ('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date), ('isStationeryIssued', '=', False)], order='posting_date ASC')
            item_journal_sales = self.env['ae.itemjournal.header'].search([('customer_name', '=', self.customer_name.customer_name), ('posting_date', '>=', self.starting_date), ('posting_date', '<=', self.ending_date)])
            customer_name = self.customer_name.customer_name

        if not inv_led_entry:
            raise UserError('No data found with the given criteria or stationery already issued.')
        
        stationery_inventory_dict = defaultdict(list)
        total_price_per_customer = defaultdict(float)
        
        for inv_led in inv_led_entry:
            total_price = (-1*inv_led.quantity) * inv_led.source_price
            vals = {
                'index': len(stationery_inventory_dict[inv_led.source_name]) + 1,
                'description': inv_led.inventory_name,
                'postingdate': inv_led.posting_date.strftime("%d-%B-%Y") if inv_led.posting_date else '',
                'quantity': inv_led.quantity * -1,
                'unit': inv_led.unit_of_measure,
                'price': "{:,.2f}".format(inv_led.source_price),
                'totalprice': "{:,.2f}".format((inv_led.quantity * -1) * inv_led.source_price),
            }
            stationery_inventory_dict[inv_led.source_name].append(vals)
            total_price_per_customer[inv_led.source_name] += (-1 * inv_led.quantity) * inv_led.source_price
        
        # Convert the dictionary to a list
        stationery_inventory_list = [{'customer_name': customer, 'sumtotalprice': total_price_per_customer[customer],'inventory_list': inventory_list}
                                     for customer, inventory_list in stationery_inventory_dict.items()]
            
        # Update the inventory ledger entry with isStationeryIssued to True
        inv_led_entry.write({'isStationeryIssued': True})

        # Update the item journal header
        item_journal_sales.write({'isStationeryIssued': True, 'stationery_document_no': 'Stationery Issued Document' + ' ' + self.customer_name.customer_name if not self.isgetallcustomer else 'Stationery Issued Document'})

        data = {
            'form_data': self.read()[0],
            'customer_name': customer_name,
            'stationery_inventory_list': stationery_inventory_list,
        }

        pdf = self.env.ref('inventorymodule.action_report_stationaryissued')._render_qweb_pdf(self.ids[0], data=data)[0]

        # Create the stationary issued list
        self.env['ae.stationery.issued.list'].create({
            'stationery_issued_document': 'Stationery Issued Document' + ' ' + self.customer_name.customer_name if not self.isgetallcustomer else 'Stationery Issued Document - All Customer',
            'stationery_issued_date': fields.Datetime.now(),
            'get_data_starting_date': self.starting_date,
            'get_data_ending_date': self.ending_date,
            'stationery_printout': base64.b64encode(pdf),
        })

        return self.env.ref('inventorymodule.action_report_stationaryissued').report_action(self, data=data)
    