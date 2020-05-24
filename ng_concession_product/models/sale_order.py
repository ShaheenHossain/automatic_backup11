from odoo import api, fields, models, exceptions, _
from math import fabs
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    return_concession = fields.Boolean(string="Return Concession")


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.depends('return_concession')
    def set_return_zero(self):
        if self.return_concession is True:
            self.price_unit = 0.00

    return_concession = fields.Boolean(string="Return Concession")

    price_unit = fields.Float(sting="Price Unit")

    @api.onchange('order_id.return_concession')
    def get_sale_state(self):
        if self.order_id.return_concession is True:
            self.write({'return_concession': True})
