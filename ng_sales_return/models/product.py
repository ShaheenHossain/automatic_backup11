from odoo import models, fields, api,_
from odoo.exceptions import UserError


class Product(models.Model):
    _inherit = 'product.template'

    concession_sor = fields.Selection(selection_add=[('sor', 'Sale/Returm Product')], string="Concession/SOR")
    partner_id = fields.Many2one('res.partner', string="Vendor", domain=[('supplier', '=', True)])
    type = fields.Selection(selection_add=[('product', 'Stockable Product')], default='product')

    @api.onchange('concession_sor')
    def set_sale_return_category(self):
        company_id = self.env.user.company_id
        if self.concession_sor == 'sor':
            self.categ_id = company_id.sor_product


class SORProductCategory(models.Model):
    _inherit = "product.category"

    sor_income_account = fields.Many2one('account.account', string="SOR Income",
                                         domain=[('user_type_id', '=', ('Income', 'Other Income'))])


