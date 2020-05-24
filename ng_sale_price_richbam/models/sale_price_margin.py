# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class SalePriceMargin(models.Model):
    """Model to manage the setting of price per category"""

    _name = 'sale.price.margin'
    _description = "Sales Price Margin"

    name = fields.Char("Description", required=True)
    product_category_id = fields.Many2one('product.category', "Product Category",
                                          domain=lambda self: [("id", "not in",
                                                                  self.search([]).mapped('product_category_id').ids)])
    perc_margin = fields.Float(string="Margin %")

    _sql_constraints = [('sale_margin_categ_uniq', 'UNIQUE (product_category_id)', 'Product category must be unique!')]

    @api.multi
    def compute_sale_price(self):
        """Compute the sales price for all the """
        for record in self:
            if record.product_category_id:
                ProductTemplates = self.env['product.template'].search([('categ_id', '=', record.product_category_id.id)])
                ProductTemplates = ProductTemplates.filtered(lambda templ: not templ.price_computed)
                for template in ProductTemplates:
                    template.write({'list_price': template.compute_sale_price(perc_margin=self.perc_margin)})
                return ProductTemplates.write({'price_computed': True})
