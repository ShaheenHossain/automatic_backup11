# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class product_template(models.Model):
    _inherit = 'product.template'

    multi_uom = fields.Boolean('Multi unit of measure')
    price_uom_ids = fields.One2many('product.uom.price', 'product_tmpl_id', string='Units of measure')