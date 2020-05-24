# -*- coding: utf-8 -*-
from odoo import http

# class NgHideUpdateQuantity(http.Controller):
#     @http.route('/ng_hide_update_quantity/ng_hide_update_quantity/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ng_hide_update_quantity/ng_hide_update_quantity/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ng_hide_update_quantity.listing', {
#             'root': '/ng_hide_update_quantity/ng_hide_update_quantity',
#             'objects': http.request.env['ng_hide_update_quantity.ng_hide_update_quantity'].search([]),
#         })

#     @http.route('/ng_hide_update_quantity/ng_hide_update_quantity/objects/<model("ng_hide_update_quantity.ng_hide_update_quantity"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ng_hide_update_quantity.object', {
#             'object': obj
#         })