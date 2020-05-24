# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

import pytz
from odoo import models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.exceptions import Warning


class MostSellingProducts(models.AbstractModel):
    _name = 'report.most_selling_product.ir_most_selling_product'

    @api.model
    def get_report_values(self, docids, data=None):
        self.begining_qty = 0.0
        self.total_in = 0.0
        self.total_out = 0.0
        self.total_int = 0.0
        self.total_adj = 0.0
        self.total_begin = 0.0
        self.total_end = 0.0
        self.total_inventory = []
        self.value_exist = {}
        return {
            'doc_ids': self._ids,
            'docs': self,
            'data': data,
            'get_warehouse_name': self.get_warehouse_name,
            'get_company': self._get_company,
            'get_product_name': self._product_name,
            'get_warehouse': self._get_warehouse,
            'get_lines': self._get_lines,
            'get_value_exist': self._get_value_exist,
            'total_in': self._total_in,
            'total_out': self._total_out,
            'total_int': self._total_int,
            'total_adj': self._total_adj,
            'total_vals': self._total_vals,
            'total_begin': self._total_begin,
            'total_end': self._total_end,
            'get_product_uom': self.get_product_uom
            }

    def get_product_uom(self, product_id):
        """
        Warehouse wise inward Qty
        """
        return self.env['product.product'].browse(product_id).uom_id.name

    def _total_in(self):
        """
        Warehouse wise inward Qty
        """
        return self.total_in

    def _total_out(self):
        """
        Warehouse wise out Qty
        """
        return self.total_out

    def _total_int(self):
        """
        Warehouse wise internal Qty
        """
        return self.total_int

    def _total_adj(self):
        """
        Warehouse wise adjustment Qty
        """
        return self.total_adj

    def _total_begin(self):
        """
        Warehouse wise begining Qty
        """
        return self.total_begin

    def _total_end(self):
        """
        Warehouse wise ending Qty
        """
        return self.total_end

    def _total_vals(self, company_id):
        """
        Grand Total Inventory
        """
        ftotal_in = ftotal_out = ftotal_int = ftotal_adj = ftotal_begin = ftotal_end = 0.0
        for data in self.total_inventory:
            for key, value in data.items():
                if key[1] == company_id:
                    ftotal_in += value['total_in']
                    ftotal_out += value['total_out']
                    ftotal_int += value['total_int']
                    ftotal_adj += value['total_adj']
                    ftotal_begin += value['total_begin']
                    ftotal_end += value['total_end']

        return ftotal_begin, ftotal_in, ftotal_out, ftotal_int, ftotal_adj, ftotal_end 

    def _get_value_exist(self, warehouse_id, company_id):
        """
        Compute Total Values
        """
        total_in = total_out = total_int = total_adj = total_begin = 0.0
        for warehouse in self.value_exist[warehouse_id]:
            total_in += warehouse.get('product_qty_in', 0.0)
            total_out += warehouse.get('product_qty_out', 0.0)
            total_int += warehouse.get('product_qty_internal', 0.0)
            total_adj += warehouse.get('product_qty_adjustment', 0.0)
            total_begin += warehouse.get('begining_qty', 0.0)

        self.total_in = total_in
        self.total_out = total_out
        self.total_int = total_int
        self.total_adj = total_adj
        self.total_begin = total_begin
        self.total_end = total_begin + total_in + total_out + total_int + total_adj
        self.total_inventory.append({
             (warehouse_id, company_id):{
                                        'total_in': total_in,
                                        'total_out': total_out,
                                        'total_int': total_int,
                                        'total_adj': total_adj,
                                        'total_begin': total_begin,
                                        'total_end': total_begin + total_in + total_out + total_int + total_adj
                                        }})
        return ''

    def _get_company(self, company_ids):
        res_company_pool = self.env['res.company']
        if not company_ids:
            company_ids = [x.id for x in res_company_pool.sudo().search([])]

        #filter to only have warehouses.
        selected_companies = []
        for company_id in company_ids:
            if self.env['stock.warehouse'].sudo().search([('company_id','=',company_id)]):
                selected_companies.append(company_id)

        return res_company_pool.browse(selected_companies).read(['name'])

    def get_warehouse_name(self, warehouse_ids):
        """
        Return warehouse names
            - WH A, WH B...
        """
        warehouse_obj = self.env['stock.warehouse']
        if not warehouse_ids:
            warehouse_ids = [x.id for x in warehouse_obj.search([])]
        war_detail = warehouse_obj.read(warehouse_ids,['name'])
        return ', '.join([lt['name'] or '' for lt in war_detail])

    def convert_withtimezone(self, userdate):
        """
        Convert to Time-Zone with compare to UTC
        """
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATETIME_FORMAT)
        tz_name = self.env.context.get('tz') or self.env.user.tz
        if tz_name:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            # not need if you give default datetime into entry ;)
            user_datetime = user_date  # + relativedelta(hours=24.0)
            local_timestamp = context_tz.localize(user_datetime, is_dst=False)
            user_datetime = local_timestamp.astimezone(utc)
            return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def location_wise_value(self, start_date, end_date, locations , value, include_zero=False):
        """
        Complete data with location wise
            - Out Qty(Outward Quantity to given location)
        Return:
            [{},{},{}...]
        """

        self._cr.execute('''
                        SELECT pp.id AS product_id,
                            sum((
                                CASE WHEN spt.code in ('outgoing') AND sm.location_id in %s 
                                THEN (sm.product_uom_qty * pu.factor / pu2.factor)
                                ELSE 0.0 
                                END
                            )) AS product_qty_out

                        FROM product_product pp 
                        LEFT JOIN  stock_move sm ON (sm.product_id = pp.id and sm.date >= %s and sm.date <= %s and sm.state = 'done' and sm.location_id != sm.location_dest_id)
                        LEFT JOIN stock_picking sp ON (sm.picking_id=sp.id)
                        LEFT JOIN stock_picking_type spt ON (spt.id=sp.picking_type_id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN product_uom pu ON (pt.uom_id = pu.id)
                        LEFT JOIN product_uom pu2 ON (sm.product_uom=pu2.id)

                        GROUP BY pp.id order by product_qty_out desc LIMIT %s 
                        ''', (tuple(locations), start_date, end_date, value))

        values = self._cr.dictfetchall()
        # Removed zero values dictionary
        if not include_zero:
            values = self._remove_zero_inventory(values)
        return values

    def _remove_zero_inventory(self, values):
        final_values = []
        for rm_zero in values:
            if rm_zero['product_qty_out'] == 0.0:
                pass
            else: final_values.append(rm_zero)
        return final_values

    def _get_warehouse(self, warehouse):
        """
        Find warehouse name with id
        """
        return self.env['stock.warehouse'].browse(warehouse).read(['name'])[0]['name']

    def _product_name(self, product_id):
        """
        Find product name and assign to it
        """
        product = self.env['product.product'].browse(product_id).name_get()
        return product and product[0] and product[0][1] or ''

    def find_warehouses(self,company_id):
        """
        Find all warehouses
        """
        return [x.id for x in self.env['stock.warehouse'].search([('company_id','=',company_id)])]

    def _find_locations(self, warehouse):
        """
        Find warehouse stock locations and its childs.
            -All stock reports depends on stock location of warehouse.
        """
        warehouse_obj = self.env['stock.warehouse']
        location_obj = self.env['stock.location']
        store_location_id = warehouse_obj.browse(warehouse).view_location_id.id
        return [x.id for x in location_obj.search([('location_id', 'child_of', store_location_id)])]

    def _compare_with_company(self, warehouse, company):
        """
        Company loop check ,whether it is in company of not.
        """
        company_id = self.env['stock.warehouse'].browse(warehouse).read(['company_id'])[0]['company_id']
        if company_id[0] != company:
            return False
        return True

    def _get_lines(self, data, company):
        """
        Process:
            Pass start date, end date, locations to get data from moves,
            Merge those data with locations,
        Return:
            {location : [{},{},{}...], location : [{},{},{}...],...}
        """

        start_date = self.convert_withtimezone(data['form']['start_date'] + ' 00:00:00')
        end_date = self.convert_withtimezone(data['form']['end_date'] + ' 23:59:59')

        warehouse_ids = data['form'] and data['form'].get('warehouse_ids', []) or []
        include_zero = data['form'] and data['form'].get('include_zero') or False
        value = data['form'] and data['form'].get('value') or 0
        if not warehouse_ids:
            warehouse_ids = self.find_warehouses(company)

        final_values = {}
        for warehouse in warehouse_ids:
            # looping for only warehouses which is under current company
            if self._compare_with_company(warehouse, company):
                locations = self._find_locations(warehouse)
                if not locations:
                    raise Warning(_(""" No Location Found!\n please check your warehouse/location configuration."""))
                final_values.update({
                                     warehouse: self.location_wise_value(start_date, end_date, locations, value, include_zero)
                                     })

        self.value_exist = final_values
        return final_values

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
