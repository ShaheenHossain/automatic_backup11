# -*- coding: utf-8 -*-
# 1 imports of python lib
# 2 imports of odoo
from odoo import _, models, fields, api
# 3 imports from odoo modules


class TruckReservations(models.Model):
    """Manage the reservations for trucks with this model."""

    _name = 'reservations.truck'
    _description = 'Truck Reservations'

    date_due = fields.Date("Date Request is due")
    date_performed = fields.Date("Date performed")
    truck_id = fields.Many2one('fleet.vehicle', "Truck")