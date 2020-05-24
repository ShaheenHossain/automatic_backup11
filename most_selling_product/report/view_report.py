# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solutions.(<https://tidyway.in/>)

from odoo import fields, models, tools


class TopSellingViewReport(models.Model):
    _name = "top.selling.view.report"
    _description = "Top Selling Products"
    _auto = False

    product_id = fields.Many2one(
         'product.product',
         'Product',
         )
    location_id = fields.Many2one(
         'stock.location',
         'Location',
         )
    product_qty_out = fields.Float(
        'Sold Quantity',
        )

    _order = 'product_qty_out desc'

    def init(self):
        tools.drop_view_if_exists(self._cr, 'top_selling_view_report')
        self._cr.execute("""
            create or replace view top_selling_view_report as (
                SELECT min(id) as id, product_id, location_id,
                sum(product_qty_out) as product_qty_out
                FROM (
                    SELECT sm.id as id, sm.product_id AS product_id,
                        sm.location_id as location_id,
                        sum((
                            CASE WHEN spt.code in ('outgoing') 
                            THEN (sm.product_uom_qty * pu.factor / pu2.factor)
                            ELSE 0.0 
                            END
                        )) AS product_qty_out
                FROM stock_move sm 
                    LEFT JOIN product_product pp ON (sm.product_id=pp.id)
                    LEFT JOIN stock_location sloc ON (sm.location_id=sloc.id)
                    LEFT JOIN stock_picking sp ON (sm.picking_id=sp.id)
                    LEFT JOIN stock_picking_type spt ON (spt.id=sp.picking_type_id)
                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                    LEFT JOIN product_uom pu ON (pt.uom_id = pu.id)
                    LEFT JOIN product_uom pu2 ON (sm.product_uom=pu2.id)
                WHERE sm.state = 'done' 
                    AND sm.location_id != sm.location_dest_id
                    AND sloc.usage in ('internal')
                GROUP BY sm.id, sm.product_id, sm.location_id 
                )as foo
            group by product_id, location_id HAVING sum(product_qty_out) > 0
            ORDER BY product_qty_out desc
            )""")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
