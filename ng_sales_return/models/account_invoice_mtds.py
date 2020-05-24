from odoo import fields, models,api,_
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class AccountInvoiceSR(models.Model):
    _inherit = 'account.invoice'

    concession_sor = fields.Selection([('sor', 'Sale/Return'), ('concession', 'Concession Product')], string="Concession/SOR")


class AccountInvoiceSRLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def income_account(self):
        res = []
        line = self
        # for line in self.invoice_line_ids:
        if not line.product_id.categ_id.sor_income_account:
            raise ValidationError(_('Kindly set a Sale/Return Account'))
        res.append({
            'invl_id': line.id,
            'type': 'src',
            'name': line.name.split('\n')[0][:64],
            'price_unit': line.price_unit,
            'quantity': line.quantity,
            'price':  line.price_subtotal - (line.product_id.standard_price * line.quantity),
            'debit': line.price_unit * line.quantity,
            'account_id': line.product_id.categ_id.sor_income_account.id,
            'product_id': line.product_id.id,
            'uom_id': line.uom_id.id,
            # 'invoice_id': self.id,
            'partner_id': line.invoice_id.partner_id.id
        })
        return res

    @api.model
    def account_payable(self):
        res = []
        record = self
        if not record.product_id.partner_id.property_account_payable_id:
            raise ValidationError(_('Kindly set a Payable Account'))
        res.append({
            'type': 'src',
            'name': record.name.split('\n')[0][:64],
            'price_unit': record.price_unit,
            'quantity': record.quantity,
            'price': record.product_id.standard_price * record.quantity,
            'credit': record.price_unit * record.quantity,
            'account_id': record.product_id.partner_id.property_account_payable_id.id,
            'partner_id': record.product_id.partner_id.id
        })
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    concession_sor = fields.Selection(add_selection=[('sor', 'Sale/Return')], string="Concession/SOR")

