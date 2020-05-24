# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning


class PosConfig(models.Model):

    _inherit = 'pos.config'

    def delete_cache(self):
        super(PosConfig, self).delete_cache()


class InvalidateWizard(models.TransientModel):

    _name = 'invalidate.wizard'
    config_ids = fields.Many2many('pos.config', string='Configurations')

    @api.multi
    def clear_cache(self):
        self.ensure_one()
        configs = self.config_ids
        try:
            configs.delete_cache()
        except Exception as e:
            raise Warning("%s!" % e)
