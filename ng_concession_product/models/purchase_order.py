from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError
from odoo.addons import decimal_precision as dp


class ConsPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def action_view_invoice(self):
        for record in self.order_line:
            if record.product_id.concession_sor == 'concession':
                raise UserError(_('Sorry, you are not allowed to do this'))
            else:
                res = super(ConsPurchaseOrder, self).action_view_invoice()
                return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))

    @api.onchange('order_id.partner_id')
    def get_product_id(self):
        domain = {}
        if self.order_id.partner_id:
            domain['product_id'] = [('partner_id.name', '=', self.order_id.partner_id.name)]
        return {'domain': domain}

    @api.onchange('product_id')
    def set_price_unit(self):
        if self.product_id.concession_sor == 'concession':
            self.price_unit = self.product_id.standard_price
