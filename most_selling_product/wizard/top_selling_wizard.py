# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

import time
from odoo import models, api, fields, _
from odoo.exceptions import Warning


class TopSellingWizard(models.TransientModel):
    _name = 'top.selling.report'

    company_id = fields.Many2one('res.company', string='Company')
    warehouse_ids = fields.Many2many('stock.warehouse', string='warehouse')
    start_date = fields.Date('Beginning Date', required=True, default=time.strftime('%Y-%m-%d'))
    end_date = fields.Date('End Date', required=True, default=time.strftime('%Y-%m-%d'))
    value = fields.Integer('Display Top Products?', help="If you want to see Top 10 selling product, then put 10 here.", required=True, default=5)
    sort_order = fields.Selection([('warehouse', 'Warehouse'), ('product_category', 'Product Category')], 'Sort Order', required=True, default='warehouse')
    include_zero = fields.Boolean('Include Zero Movement?', help="True, if you want to see zero movements of products.\nNote: It will consider only movements done in-between dates.")

    @api.onchange('company_id')
    def onchange_company_id(self):
        """
        Make warehouse compatible with company
        """
        domain = {}
        self.warehouse_ids = False
        if self.company_id:
            warehouse_ids = self.env['stock.warehouse'].sudo().search([('company_id', '=', self.company_id.id)])
            domain = {'domain':{'warehouse_ids': [('id', 'in', [y.id for y in warehouse_ids])]}}
        return domain

    @api.multi
    def print_report(self):
        """
            Print report either by warehouse or product-category
        """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        datas = {
                 'form': 
                        {
                            'company_id': self.company_id and [self.company_id.id] or [],
                            'warehouse_ids': [y.id for y in self.warehouse_ids],
                            'start_date': self.start_date,
                            'end_date': self.end_date,
                            'include_zero': self.include_zero,
                            'sort_order': self.sort_order,
                            'value':  self.value,
                            'id': self.id,
                        }
                }

        if [y.id for y in self.warehouse_ids] and (not self.company_id):
            self.warehouse_ids = []
            raise Warning(_('Please select company of those warehouses to get correct view.\nYou should remove all warehouses first from selection field.'))
        return self.env.ref(
                            'most_selling_product.action_ir_most_selling_product'
                            ).report_action(self, data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
