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

from openerp import models, fields, api, _


class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def disp_prod_stock(self, product_id, shop_id):
        stock_line = []
        total_qty = 0
        shop_qty = 0
        quant_obj = self.env['stock.quant']
        for warehouse_id in self.search([]):
            product_qty = 0.0
            ware_record = warehouse_id
            location_id = ware_record.lot_stock_id.id
            if shop_id:
                loc_ids1 = self.env['stock.location'].search(
                    [('location_id', 'child_of', [shop_id])])
                stock_quant_ids1 = quant_obj.search([('location_id', 'in', [
                                                    loc_id.id for loc_id in loc_ids1]), ('product_id', '=', product_id)])
                for stock_quant_id1 in stock_quant_ids1:
                    shop_qty = stock_quant_id1.quantity

            loc_ids = self.env['stock.location'].search(
                [('location_id', 'child_of', [location_id])])
            stock_quant_ids = quant_obj.search([('location_id', 'in', [
                                               loc_id.id for loc_id in loc_ids]), ('product_id', '=', product_id)])
            for stock_quant_id in stock_quant_ids:
                product_qty += stock_quant_id.quantity
            stock_line.append([ware_record.name, product_qty,ware_record.lot_stock_id.id])
            total_qty += product_qty
        return stock_line, total_qty, shop_qty


class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def do_detailed_discard_product(self, vals):
        move_lines = []
        line = []
        if vals and vals.get('data'):
            for move_line in vals.get('data').get('moveLines'):
                move_line_dict = {
                    'product_uom_id': move_line.get('product_uom'),
                    'product_id': move_line.get('product_id'),
                    'qty_done': move_line.get('product_uom_qty'),
                    'location_id': move_line.get('location_id'),
                    'location_dest_id': move_line.get('location_dest_id'),
                }
                line.append((0,0,move_line_dict))
                move_lines.append((0,0,move_line))
            picking_id = self.create({
                'location_id': vals.get('data').get('location_src_id'),
                'location_dest_id': vals.get('data').get('location_dest_id'),
                'move_type': 'direct',
                'picking_type_id':vals.get('data').get('picking_type_id'),
                'move_line_ids': line,
                'move_lines': move_lines
            })
            picking_id.action_assign()
            if picking_id:
                if vals.get('data').get('state') == 'done':
                    picking_id.action_confirm()
                    picking_id.force_assign()
                    picking_id.button_validate()
                    stock_transfer_id = self.env['stock.immediate.transfer'].search([('pick_ids', '=', picking_id.id)], limit=1)
                    if stock_transfer_id:
                        stock_transfer_id.process()
        return [picking_id.id,picking_id.name]

class stock_location(models.Model):
    _inherit = 'stock.location'

    category_ids = fields.Many2many("pos.category",string="Category")
    product_ids = fields.Many2many("product.product",string="Product")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: