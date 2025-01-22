from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class aeStationeryIssuedList(models.Model):
    _name = 'ae.stationery.issued.list'
    _description = 'Stationery Issued List'
    _rec_name = 'stationery_issued_document'
    _order = 'create_date desc'

    active = fields.Boolean(default=True)
    stationery_issued_document = fields.Char(string='Stationery Issued Document', required=True)
    stationery_issued_date = fields.Datetime(string='Stationery Issued Date', required=True)
    stationery_printout = fields.Binary(string='Stationery Printout')
    get_data_starting_date = fields.Date(string='Starting Date')
    get_data_ending_date = fields.Date(string='Ending Date')

class aeRollbackStationeryIssued(models.TransientModel):
    _name = 'ae.rollback.stationery.issued'
    _description = 'Rollback Stationery Issued'

    start_date = fields.Date(string='Starting Date', required=True)
    end_date = fields.Date(string='Ending Date', required=True)

    def action_rollback(self):
        inv_led_entry = self.env['ae.inventory.ledger.entry'].search([('entry_type', 'in', [10,11]), ('posting_date', '>=', self.start_date), ('posting_date', '<=', self.end_date), ('isStationeryIssued', '=', True)])
        item_journal_sales = self.env['ae.itemjournal.header'].search([('entry_type', 'in', [5]), ('posting_date', '>=', self.start_date), ('posting_date', '<=', self.end_date), ('isStationeryIssued', '=', True)])
        if inv_led_entry:
            for rec in inv_led_entry:
                rec.isStationeryIssued = False
        if item_journal_sales:
            for rec in item_journal_sales:
                rec.isStationeryIssued = False
                rec.stationery_document_no = False
        return True