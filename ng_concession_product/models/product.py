from odoo import models, fields, api,_
from odoo.exceptions import UserError


class ConcessionProduct(models.Model):
    _inherit = 'product.template'

    concession_sor = fields.Selection([('concession', 'Concession Product')], string="Concession/SOR")

    partner_id = fields.Many2one('res.partner', string="Vendor", domain=[('supplier', '=', True)])

    type = fields.Selection(selection_add=[('product', 'Stockable Product')], default='product')

    commission_type = fields.Selection([('percentage', 'Percentage'), ('amount', 'Amount')], default='amount',
                                       string="Commission Type")

    percentage_rate = fields.Integer(string="Percentage")

    commission = fields.Float(string="Commission")

    net_payable = fields.Float(string="Consignor Net Payable")

    @api.onchange('standard_price', 'percentage_rate')
    def set_consignee_commission(self):
        if self.standard_price and self.percentage_rate:
            self.commission = (float(self.percentage_rate) / 100) * self.standard_price

    @api.onchange('standard_price', 'commission')
    def set_consignor_commission(self):
        if self.standard_price and self.commission:
            self.net_payable = self.standard_price - float(self.commission)

    @api.onchange('concession_sor')
    def set_product_category(self):
        company_id = self.env.user.company_id
        if self.concession_sor == 'concession':
            self.categ_id = company_id.concession_product


class ProductCategory(models.Model):
    _inherit = "product.category"

    commission_account = fields.Many2one('account.account', string="Commission A/C",
                                         domain=[('user_type_id', '=', ('Income', 'Other Income'))])

    other_income_account = fields.Many2one('account.account', string="Other Income",
                                           domain=[('user_type_id', '=', ('Income', 'Other Income'))])
