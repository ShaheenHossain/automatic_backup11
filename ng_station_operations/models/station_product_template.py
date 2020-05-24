from odoo import api, fields, models, exceptions


class product_template(models.Model):
    _inherit = "product.template"
    _description = "Product"

    is_petroleum = fields.Boolean("Is Petroleum", default=False)

    @api.onchange('petroleum_product')
    def get_name(self):
        for record in self:
            record.name = record.petroleum_product

    type = fields.Selection(selection_add=[('product', 'Stockable Product')], default='product')
