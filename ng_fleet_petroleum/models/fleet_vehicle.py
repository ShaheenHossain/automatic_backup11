# -*- coding: utf-8 -*-
from odoo import _, models, fields, api


class FleetTruck(models.Model):
    """
    Class for managing the request for trucks

    ...

    Attributes
    ----------
    _inherit : str
        Model that we're extending
    state : str
        State of the document at a particular time
    reservation_ids : list of ids
        reservations booked against the particular truck
    capacity : float
        capacity of truck

    """

    _inherit = 'fleet.vehicle'
    state = fields.Selection(selection=[
        ('available', "Awaiting Dispatch"),
        ('dispatched', "Dispatched"),
        ('at_depot', "Arrived Depot"),
        ('left_depot', "Departed Depot"),
        ], 
        string='States', track_visibility='always', default="available")
    reservation_ids = fields.One2many('reservations.truck', 'truck_id', "Reservations")
    capacity = fields.Float("Truck capacity")
    product_id = fields.Many2one('product.product', "Product")
    product_uom_id = fields.Many2one('product.uom', "Capacity",
                                     default=lambda self: self.env['product.uom'].search([('name', 'ilike', "lit%")],
                                                                                         limit=1))
    is_warehouse = fields.Boolean("Is Warehouse")

    @api.onchange('is_warehouse')
    def _onchange_is_warehouse(self):
        """If truck is marked as warehouse, create a corresponding warehouse at the Head Office"""
        if self.is_warehouse:
            StockWarehouse = self.env['stock.warehouse']
            default_fields = StockWarehouse.default_get(['active', 'company_id', 'partner_id', 'view_location_id',
                                                         'lot_stock_id', 'code', 'reception_steps', 'delivery_steps'])
            truck_name = self.model_id.name
            default_fields['name'] = truck_name
            name_split = truck_name.split(" ")
            code = ''
            for name in name_split:
                code += name[0]
            if len(code) == 1:
                code = code + truck_name[1]
            code = code.upper()
            default_fields['is_truck'] = True
            default_fields['code'] = code
            default_fields['product_id'] = self.product_id.id if self.product_id else ''
            head_office = self.env['res.company'].get_head_office()
            default_fields['company_id'] = head_office.id
            # Check if there is a warehouse with same name
            if StockWarehouse.sudo().search([('name', '=', truck_name), ('code', '=', code)]):
                pass
            else:
                StockWarehouse.sudo().create(default_fields)

    @api.model
    def create(self, vals):
        if 'is_warehouse' in vals:
            if 'is_warehouse':
                StockWarehouse = self.env['stock.warehouse']
                default_fields = StockWarehouse.default_get(['active', 'company_id', 'partner_id', 'view_location_id',
                                                             'lot_stock_id', 'code', 'reception_steps', 'delivery_steps'])
                truck_name = self.env['fleet.vehicle.model'].browse(vals['model_id']).name
                default_fields['name'] = truck_name
                name_split = truck_name.split(" ")
                code = ''
                for name in name_split:
                    code += name[0]
                if len(code) == 1:
                    code = code + truck_name[1]
                code = code.upper()
                default_fields['is_truck'] = True
                default_fields['code'] = code
                default_fields['product_id'] = self.env['product.product'].browse(vals['product_id']).id if \
                    vals.get('product_id') else ''
                head_office = self.env['res.company'].get_head_office()
                default_fields['company_id'] = head_office.id
                # Check if there is a warehouse with same name
                if StockWarehouse.sudo().search([('name', '=', truck_name), ('code', '=', code)]):
                    pass
                else:
                    StockWarehouse.sudo().create(default_fields)
        return super(FleetTruck, self).create(vals)
