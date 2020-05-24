from odoo import api, fields, models, _


class res_partner(models.Model):
    _inherit = "res.company"

    sor_product = fields.Many2one('product.category', string="SOR Product Category")
    concession_product = fields.Many2one('product.category', string="Concession Product Category")


