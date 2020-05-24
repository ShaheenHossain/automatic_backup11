# -*- coding: utf-8 -*-
from odoo import http

# class NgFlexiretailComAdvance(http.Controller):
#     @http.route('/ng_flexiretail_com_advance/ng_flexiretail_com_advance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ng_flexiretail_com_advance/ng_flexiretail_com_advance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ng_flexiretail_com_advance.listing', {
#             'root': '/ng_flexiretail_com_advance/ng_flexiretail_com_advance',
#             'objects': http.request.env['ng_flexiretail_com_advance.ng_flexiretail_com_advance'].search([]),
#         })

#     @http.route('/ng_flexiretail_com_advance/ng_flexiretail_com_advance/objects/<model("ng_flexiretail_com_advance.ng_flexiretail_com_advance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ng_flexiretail_com_advance.object', {
#             'object': obj
#         })