from odoo import models, fields, api, _

class InventoryLedgerEntry(models.Model):
    _name = 'ae.inventory.ledger.entry'
    _description = 'Inventory Ledger Entry'
    _rec_name = 'document_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'posting_date desc'

    active = fields.Boolean(default=True)
    
    inventory_id = fields.Many2one('ae.inventory', string='Inventory')
    inventory_name = fields.Char(string='Inventory Name')
    entry_no = fields.Integer(string='Entry No.')
    document_no = fields.Char(string='Document No.')
    inventory_number = fields.Char(string='Inventory Number')
    posting_date = fields.Datetime(string='Posting Date')
    entry_type = fields.Selection([('1', 'Inventory Update'), ('2', 'Stock In'), ('3', 'Stock Out'), ('4', 'Movement'),('5', 'Auction'),('6', 'Write Off'),('7', 'Destroyed'),('8', 'Consumption'),('9', 'Purchase'), ('10', 'Sales'), ('11', 'Sales Return'), ('12', 'Delivery'), ('13', 'Loss'), ('14', 'Settling Out'), ('16', 'Return'), ('17', 'Auction Storage')], string='Entry Type')
    inventory_type = fields.Selection([
        ('1', 'Inventory'),
        ('2', 'Asset'),
        ('3', 'Attractive Items'),
        ('4', 'Stationary & Supplies'),
        ('5', 'Settling Kit'),
    ], string='Inventory Type')
    asset_number = fields.Char(string='Asset Number')
    inventory_label = fields.Char(string='Inventory Label')
    location_code = fields.Char(string='Location Code')
    room_code = fields.Char(string='Room Code')
    sub_room_code = fields.Char(string='Sub Room Code')
    quantity = fields.Integer(string='Quantity')
    unit_of_measure = fields.Char(string='Unit of Measure')
    aucquisition_value = fields.Char(string='Aucquisition Value')
    aucquisition_date = fields.Date(string='Aucquisition Date')
    inventory_group = fields.Many2one('ae.inventory.master.group', string='Inventory Group')
    height = fields.Integer(string='Height')
    width = fields.Integer(string='Width')
    length = fields.Integer(string='Length')
    serial_number = fields.Char(string='Serial Number')
    electrical = fields.Boolean(string='Electrical')
    test_date = fields.Date(string='Test Date')
    expired_date = fields.Date(string='Expired Date')
    tagging_id = fields.Char(string='Tagging ID')
    tagger_name = fields.Char(string='Tagger Name')
    source_price = fields.Integer(string='Source Price')
    source_no = fields.Char(string='Source No.')
    source_name = fields.Char(string='Source Name')
    remarks = fields.Text(string='Remarks')
    from_location_code = fields.Many2one('ae.location', string='From Location Code')
    to_location_code = fields.Many2one('ae.location', string='To Location Code')
    updated_by = fields.Many2one('res.users', string='Updated By')
    updated_date = fields.Date(string='Updated Date', default=fields.Date.today())
    line_no = fields.Char(string='Line No.')
    vendor_name = fields.Many2one('ae.master.vendor', string='Vendor Name')
    purchase_date = fields.Date(string='Purchase Date')
    delivery_date = fields.Datetime(string='Delivery Date')
    returned_date = fields.Datetime(string='Returned Date')
    return_quantity = fields.Integer(string='Return Quantity')
    document_type = fields.Selection([('1', 'Item Journal'), ('2', 'Settling Kit'), ('3', 'Auction'), ('4', 'Movement'), ('5', 'Disposal')], string='Document Type')
    isStationeryIssued = fields.Boolean(string='Is Stationery Issued')
    qty_has_returned = fields.Integer(string='Qty Has Returned')
    actual_qty = fields.Integer(string='Actual Qty')
    qty_sales = fields.Integer(string='Qty Sales')
    source_price_purchase = fields.Integer(string='Source Price Purchase')
    ratio_purchase = fields.Integer(string='Ratio Purchase', track_visibility='always')