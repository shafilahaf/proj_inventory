from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class auction_report_wizard(models.TransientModel):
    _name = 'ae.inventory.auction.report.wizard'
    _description = 'Auction Report Wizard'

    date_filter= fields.Date(string='Date Filter', required=True)
    get_month_year = fields.Char(string='Month/Year', compute='_compute_month_year', store=True)

    @api.depends('date_filter')
    def _compute_month_year(self):
        for rec in self:
            rec.get_month_year = rec.date_filter.strftime("%d %B %Y")
            rec.get_month_year = rec.get_month_year.upper()

    def action_print_report(self):
        domain = []
        domain.append(('posting_date', '=', self.date_filter))

        auctionheaders = self.env['ae.auction.header'].search(domain, order='lot_no')
        
        if not auctionheaders:
            raise UserError('No Auction Report found for the specified criteria.')

        auction_list = []
        prev_lotno = ""
        totalhargalimit= 0
        totalhargaterbentuk = 0
       
        for index, auctionheader in enumerate(auctionheaders):
            actionlines = self.env['ae.auction.line'].search([('auction_header_id', '=', auctionheader.id)])
            
            totalhargalimit = totalhargalimit + auctionheader.harga_limit
            totalhargaterbentuk = totalhargaterbentuk + auctionheader.harga_terbentuk
            for actionline in actionlines:
                vals = {
                    'lotno': auctionheader.lot_no if auctionheader.lot_no != prev_lotno else '',
                    'hargalimit': "{:,.0f}".format(auctionheader.harga_limit)   if auctionheader.lot_no != prev_lotno else '',
                    'namabarang' : actionline.inventory.inventory_name,
                    'quantity': actionline.quantity,
                    'hargaterbentuk': "{:,.0f}".format(auctionheader.harga_terbentuk)  if auctionheader.lot_no != prev_lotno else '',
                    'reccount' : len(actionlines),
                    'totallimit' : "{:,.0f}".format(totalhargalimit)  ,
                    'totalterbentuk' : "{:,.0f}".format(totalhargaterbentuk) ,
                }
                auction_list.append(vals)
                prev_lotno = auctionheader.lot_no

        data = {
            'form_data' : self.read()[0],
            'auctiondatas' : auction_list,
        }
        return self.env.ref('inventorymodule.action_report_auction').report_action(self, data=data)