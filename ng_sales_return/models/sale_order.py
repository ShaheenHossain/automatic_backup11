from odoo import api, fields, models, exceptions, _
from math import fabs
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    return_product = fields.Boolean(string="Return Product")

    # @api.multi
    # def action_view_invoice(self):
    #     invoices = self.mapped('invoice_ids')
    #     print("*******", invoices)
    #     for record in invoices.invoice_line_ids:
    #         invoices.sale_return = record.product_id.sale_return
    #     action = self.env.ref('account.action_invoice_tree1').read()[0]
    #     if len(invoices) > 1:
    #         action['domain'] = [('id', 'in', invoices.ids)]
    #     elif len(invoices) == 1:
    #         action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
    #         action['res_id'] = invoices.ids[0]
    #     else:
    #         action = {'type': 'ir.actions.act_window_close'}
    #     return action

    # @api.multi
    # def action_confirm(self):
    #     if self.return_product is True:
    #         for record in self.order_line:
    #             if record.product_id.partner_id.name != self.partner_id.name:
    #                 raise exceptions.UserError(_("Product does not belong to the Vendor"))
    #     res = super(SaleOrder, self).action_confirm()
    #     return res


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    return_product = fields.Boolean(string="Discharge")

    @api.onchange('order_id.return_product')
    def get_sale_state(self):
        if self.order_id.return_product is True:
            self.write({'return_product': True, 'price_unit': 0.00})
