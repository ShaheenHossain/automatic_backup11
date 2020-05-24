# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Fleet Management - Richbam',
    'website' : 'https://www.mattobell.com',
    'author' : """Matt O'Bell""",
    'summary' : 'Vehicle, leasing, insurances, costs',
    'description' : """
        With this module, we manage the activities of the fleet department of Richbam,
        contracts associated to those vehicle as well as services, fuel log
        entries, costs and many other features necessary to the management 
        of your fleet of vehicle(s)

        Main Features
        * Add vehicles to your fleet
        * Manage contracts for vehicles
        * Reminder when a contract reach its expiration date
        * Add services, fuel log entry, odometer values for all vehicles
        * Show all costs associated to a vehicle or to a type of service
        * Analysis graph for costs
        """,
    'depends': [
        'sale',
        'fleet',
        'ng_station_operations',
    ],
    'data': [
        'security/access_groups.xml',
        'security/ir.model.access.csv',
        'security/access_trucking_operations.xml',
        'views/res_company_view.xml',
        'data/ir_sequence_data.xml',
        'views/truck_in_order_view.xml',
        'views/truck_out_order_view.xml',
        'views/truck_request_view.xml',
        'views/pricing_template_view.xml',
        'views/fleet_vehicle_view.xml',
        'views/truck_reservations_view.xml',
        'data/truck_request_email.xml',
        'views/station_charges_view.xml',
        'views/account_invoice.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}