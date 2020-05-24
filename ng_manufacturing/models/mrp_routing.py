from odoo import fields, models, api, _


class mrp_routing(models.Model):
    _inherit = 'mrp.routing'

    writeoff_account_id = fields.Many2one('account.account', string='Write Off Account')
    journal_id = fields.Many2one('account.journal', string='Account Journal')