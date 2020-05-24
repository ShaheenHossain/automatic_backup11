from odoo import fields, models, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def concession_account_payable(self):
        res = []
        record = self
        if not record.product_id.partner_id.property_account_payable_id.id:
            raise UserError(_('Please create consignor net payable account.'))
        else:
            res.append({
                'type': 'src',
                'name': record.name.split('\n')[0][:64],
                'quantity': record.quantity,
                'price': record.product_id.net_payable * record.quantity,
                'account_id': record.product_id.partner_id.property_account_payable_id.id,
                'partner_id': record.product_id.partner_id.id
            })
        return res

    @api.model
    def credit_commission(self):
        res = []
        record = self

        if not record.product_id.categ_id.commission_account:
            raise UserError(_('Please create commission account.'))
        else:
            res.append({
                'type': 'src',
                'name': record.name.split('\n')[0][:64],
                'quantity': record.quantity,
                'price': record.product_id.commission * record.quantity,
                'account_id': record.product_id.categ_id.commission_account.id,
            })
        return res

    @api.model
    def credit_other_income(self):
        res = []
        record = self

        if not record.product_id.categ_id.other_income_account:
            raise UserError(_('Please create other income account.'))
        else:
            res.append({
                'type': 'src',
                'name': record.name.split('\n')[0][:64],
                'quantity': record.quantity,
                'price': record.price_subtotal - (record.product_id.standard_price * record.quantity),
                'account_id': record.product_id.categ_id.other_income_account.id,
            })
        return res


class AccountInvoiceConcession(models.Model):
    _inherit = 'account.invoice'

    concession_sor = fields.Selection([('sor', 'Sale/Return'), ('concession', 'Concession Product')], string="Concession/SOR")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    concession_sor = fields.Selection([('concession', 'Concession Product')], string="Concession/SOR")



