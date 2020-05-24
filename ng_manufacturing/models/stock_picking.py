# -*-encoding: utf-8 -*-
from odoo import models, fields, api, _


class StockingPicking(models.Model):
    
    _inherit = 'stock.picking'
    mrp_id = fields.Many2one('mrp.production', "Production")