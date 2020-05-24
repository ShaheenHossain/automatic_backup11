# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):

    _inherit = "product.template"

    price_computed = fields.Boolean(string="Price computed", default=False)

    @api.multi
    def compute_sale_price(self, perc_margin=0.0):
        """Compute the sale price"""
        new_sale_price = self.standard_price * ((100 + perc_margin) / 100)
        return new_sale_price

    @api.model
    def create(self, values):
        template = super(ProductTemplate, self).create(values)
        return template

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        """Set the selling price when the product category changes"""
        price_margin = self.env['sale.price.margin'].search([('product_category_id', '=', self.categ_id.id)])
        if price_margin:
            self.list_price = self.compute_sale_price(perc_margin=price_margin.perc_margin)
            self.price_computed = True
        else:
            self.price_computed = False
