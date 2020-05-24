from odoo import fields, models,api,_
from odoo.exceptions import UserError, AccessError
import time


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        # account_move = self.env['account.move']
        # account_move_line = self.env['account.move.line'].with_context(check_move_validity=False)
        #
        # for record in self.move_lines:
        #     if (record.product_id.sale_return is True) and (self.picking_type_id.name == 'Delivery Orders'):
        #         move = account_move.create({
        #             'journal_id': 1,
        #             'date': time.strftime('%Y-%m-%d'),
        #         })
        #         account_move_line.create({
        #             'account_id': record.product_id.categ_id.property_stock_valuation_account_id.id,
        #             'name': self.name,
        #             'credit': 0.0,
        #             'debit': 0.0,
        #             'move_id': move.id,
        #             'qty': record.quantity_done
        #
        #         })
        #
        #         account_move_line.create({
        #             'account_id': record.product_id.categ_id.property_stock_account_output_categ_id.id,
        #             'name': self.name,
        #             'credit': 0.0,
        #             'debit': 0.0,
        #             'move_id': move.id,
        #             'qty': record.quantity_done
        #
        #         })
        #         move.post()

        res = super(StockPicking, self).button_validate()
        return res
