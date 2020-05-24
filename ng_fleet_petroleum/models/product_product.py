# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductProduct(models.Model):

    _inherit = 'product.product'
    is_petroleum = fields.Boolean('Is Petroleum', related='product_tmpl_id.is_petroleum', store=True, copy=False)
