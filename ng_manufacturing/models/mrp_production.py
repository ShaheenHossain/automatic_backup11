from odoo import models, fields, api, _
import time


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    total_cost_wc = fields.Float(string='Total Workcenter Cost', digits=(16, 3)
        # readonly=True
    )
    raw_cost = fields.Float(string='Total Raw Material Cost', digits=(16, 3)
        # readonly=True
    )
    total_cost = fields.Float(string='Total Production Cost', digits=(16, 3)
        # readonly=True
    )
    total_cost_unit = fields.Float(string='Cost per Unit', digits=(16, 3)
        # readonly=True
    )
    wip_amount = fields.Float(string='WIP Amount')
    picking_ids = fields.One2many('stock.picking', 'mrp_id', 'Picking IDs')
    mirror_center = fields.Many2one('mrp.workcenter', string="Workcenter", related='routing_id.operation_ids.workcenter_id')
    initial_price = fields.Float(string="Initial Price")
    initial_qty = fields.Float(string="Initial Qty")
    corrected = fields.Boolean('Corrected', copy=False)

    @api.onchange('routing_id')
    def get_workcenter(self):
        if self.routing_id:
            self.mirror_center = self.routing_id.operation_ids.workcenter_id.id

    @api.multi
    def button_mark_done(self):
        self.ensure_one()
        """This writes the initial price and quantity to a dummy field""" 
        self.write({
            'initial_price': self.product_id.standard_price,
            'initial_qty': self.product_id.qty_available,
        })

        res = super(MrpProduction, self).button_mark_done()
        for picking in self.picking_ids:
            # Set picking state to confirm
            picking.write({'origin': self.name})
            picking.action_confirm()

        # ###########################################################################################
        # Updates The Total workcenter cost, total raw material, total cost and cost per unit
        #############################################################################################
        get_routing = self.env['mrp.routing'].search([('name', '=', self.routing_id.name)])

        total_cost_wc = 0.0
        for record in get_routing.operation_ids:
            total_cost_wc += (record.workcenter_id.labor_cost + record.workcenter_id.electric_cost +
                              record.workcenter_id.consumables_cost + record.workcenter_id.rent_cost +
                              record.workcenter_id.other_cost) * self.product_qty

        raw_cost = 0.0
        for record in self.move_raw_ids:
            raw_cost += record.product_uom_qty * record.product_id.standard_price

        self.write({
            'raw_cost': raw_cost,
            'total_cost_wc': total_cost_wc,
            'total_cost': raw_cost + total_cost_wc,
            'total_cost_unit': (raw_cost + total_cost_wc) / self.product_qty
        })

        """Calls the manufacturing journal method which raises journal for total costs"""
        if not self.corrected:
            self.manufacturing_journal()
        return res

    def manufacturing_journal(self):
        """Raises Journal for Total Cost"""
        self.ensure_one()
        self.set_average_cost()
        acc_move_obj = self.env['account.move']
        acc_move_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)

        costs_account = ['labor_cost_id', 'electric_cost_id', 'consumables_cost_id', 'rent_cost_id', 'other_cost_id']
        costs = ['labor_cost', 'electric_cost', 'consumables_cost', 'rent_cost', 'other_cost']

        acc_move = acc_move_obj.create({
            'journal_id': self.mirror_center.mrp_journal_id.id,
            'date': time.strftime('%Y-%m-%d'),
        })

        for record_cost, record_acc in zip(costs, costs_account):
            acc_move_line_obj.create({
                'account_id': self.product_id.categ_id.property_stock_valuation_account_id.id,
                'credit': 0.0,
                'debit': self.mirror_center[record_cost] * self.product_qty,
                'move_id': acc_move.id,
                'name': self.name
            })

            if self.mirror_center[record_acc]:
                acc_move_line_obj.create({
                    'account_id': self.mirror_center[record_acc].id,
                    'credit': self.mirror_center[record_cost] * self.product_qty,
                    'debit': 0.0,
                    'move_id': acc_move.id,
                    'name': self.name
                })
        acc_move.post()

    def set_average_cost(self):
        """Sets the standard price of product based on the following calculation"""
        self.ensure_one()
        average_cost = ((self.initial_price * self.initial_qty) + (self.product_qty * self.total_cost_unit))/(self.product_id.qty_available)
        self.product_id.write({'standard_price': average_cost})
        self.corrected = True

        """Sets the Average Cost of Finished Product and the Move Cost on the Stock Move"""
        stock_move = self.env['stock.move']
        finished_product = stock_move.search([('origin', '=', self.name), ('product_id', '=', self.product_id.name)])
        finished_product.write({'average_cost': average_cost, 'move_cost': self.total_cost_unit})
        self.raw_move_costs()

    def raw_move_costs(self):
        """Sets the move cost for each of the materials used to produce the finished product on the stock move"""
        self.ensure_one()
        stock_move = self.env['stock.move']
        for record in self.move_raw_ids:
            raw_materials = stock_move.search([('origin', '=', self.name), ('product_id', '=', record.product_id.name)])
            raw_materials.write({'move_cost': record.product_id.standard_price})
        self.correct_journal_entry()

    def correct_journal_entry(self):
        self.ensure_one()
        acc_obj = self.env['account.move']
        acc_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)

        mo_raw_cost = self.raw_cost
        valuation_cost = self.product_qty * self.initial_price

        account_move = acc_obj.create({
            'journal_id': self.product_id.categ_id.property_stock_journal.id,
            'date': fields.Datetime.now(),

        })

        if valuation_cost > mo_raw_cost:
            acc_line_obj.create({
                'account_id': self.product_id.categ_id.property_stock_valuation_account_id.id,
                'name': self.name,
                'credit': valuation_cost - mo_raw_cost,
                'debit': 0.0,
                'move_id': account_move.id

            })

            acc_line_obj.create({
                'account_id': self.product_id.categ_id.property_stock_account_input_categ_id.id,
                'name': self.name,
                'credit': 0.0,
                'debit': valuation_cost - mo_raw_cost,
                'move_id': account_move.id

            })
        else:
            acc_line_obj.create({
                'account_id': self.product_id.categ_id.property_stock_account_input_categ_id.id,
                'name': self.name,
                'credit': mo_raw_cost - valuation_cost,
                'debit': 0.0,
                'move_id': account_move.id

            })

            acc_line_obj.create({
                'account_id': self.product_id.categ_id.property_stock_valuation_account_id.id,
                'name': self.name,
                'credit': 0.0,
                'debit': mo_raw_cost - valuation_cost,
                'move_id': account_move.id

            })
        account_move.post()





