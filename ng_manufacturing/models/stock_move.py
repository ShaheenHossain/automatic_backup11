from odoo import fields, models, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    average_cost = fields.Float(string="Move Average Cost", digits=(16, 3))
    move_cost = fields.Float(string="Move Cost", digits=(16, 3))
