# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class pos_session(models.Model):
    _inherit = 'pos.session'

    @api.model
    def create(self,vals):
        res = super(pos_session, self).create(vals)
        res.branch_id = res.config_id.branch_id.id
        return res

    branch_id = fields.Many2one('res.branch', 'Branch')

class pos_order(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self,vals):
        res = super(pos_order, self).create(vals)
        res.branch_id = res.session_id.branch_id.id
        return res

    branch_id = fields.Many2one('res.branch', 'Branch')

class pos_config(models.Model):
    _inherit = 'pos.config'

    branch_id = fields.Many2one('res.branch', 'Branch')


    @api.multi
    @api.constrains('branch_id','stock_location_id')
    def _check_branch_constrains(self):
        if self.branch_id and self.stock_location_id:
            if self.branch_id.id != self.stock_location_id.branch_id.id:
                raise UserError(_('Configuration error\nYou  must select same branch on a location as asssigned on a point of sale configuration.'))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
