from odoo import api, fields, models, _


class res_partner(models.Model):
    _inherit = "res.company"

    income_account = fields.Many2one('account.account', string="Income Account")
    expense_account = fields.Many2one('account.account', string="Expense Account")
    price_difference_account = fields.Many2one('account.account', string="Price Difference Account")


