# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import models, api, fields, _
from datetime import datetime


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        if res:
            if not vals.get('barcode') and self.env['ir.config_parameter'].sudo().get_param('gen_ean13'):
                barcode_str = self.env['barcode.nomenclature'].sanitize_ean("%s%s" % (res.id, datetime.now().strftime("%d%m%y%H%M")))
                res.write({'barcode': barcode_str})
        return res
    
    @api.model
    def create_from_ui(self, product):
        if product.get('image'):
            product['image'] = product['image'].split(',')[1]
        id = product.get('id')
        if id:
            product_tmpl_id = self.env['product.product'].browse(id).product_tmpl_id
            if product_tmpl_id:
                product_tmpl_id.write(product)
        else:
            id = self.env['product.product'].create(product).id
        return id
    
    is_packaging = fields.Boolean("Is Packaging")
    loyalty_point = fields.Integer("Loyalty Point")
    is_dummy_product = fields.Boolean("Is Dummy Product")

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if res:
            if not vals.get('barcode') and self.env['ir.config_parameter'].sudo().get_param('gen_ean13'):
                barcode_str = self.env['barcode.nomenclature'].sanitize_ean("%s%s" % (res.id, datetime.now().strftime("%d%m%y%H%M")))
                res.write({'barcode': barcode_str})
        return res

    @api.model
    def calculate_product(self,config_id):
        user_allowed_company_ids = self.env.user.company_ids.ids
        config = self.env['pos.config'].browse(config_id)
        product_ids = False
        setting = self.env['res.config.settings'].search([], order='id desc', limit=1, offset=0)
        pos_session = self.env['pos.session'].search([('config_id','=',config.id),('state','=','opened')],limit=1)
        if pos_session and config.multi_store and pos_session.store_id:
            product_ids = pos_session.get_products_category_data(config_id)
            return product_ids
        else:
            if setting and setting.group_multi_company and not setting.company_share_product:
                product_ids = self.search([('product_tmpl_id.sale_ok', '=', True),('active', '=', True),
                                   ('product_tmpl_id.active', '=', True),
                                   '|',('product_tmpl_id.company_id', 'in', user_allowed_company_ids),
                                   ('product_tmpl_id.company_id', '=', False),
                                   ('available_in_pos', '=', True)])
            else:
                product_ids = self.search([('product_tmpl_id.sale_ok', '=', True),('active', '=', True),
                               ('product_tmpl_id.active', '=', True),
                               ('available_in_pos', '=', True)])
        if product_ids:
            return product_ids.ids
        else:
            return []

class product_category(models.Model):
    _inherit = "pos.category"

    loyalty_point = fields.Integer("Loyalty Point")
    return_valid_days = fields.Integer("Return Valid Days")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
