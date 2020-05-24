import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class MrpBom(models.Model):
    """ Defines bills of material for a product or a product template """
    _inherit = 'mrp.bom'

    date_start = fields.Date(string="Start Date")
    date_until = fields.Date(string="Date Until")


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.onchange('product_id')
    def get_bom(self):
        if self.product_id:
            if self.bom_id.date_until:
                if self.bom_id.date_until >= time.strftime(DEFAULT_SERVER_DATE_FORMAT):
                    raise UserError(_('Product Not Available'))
