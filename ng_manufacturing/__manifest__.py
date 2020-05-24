{
    'name': 'Extended Manufacturing Process',
    'version': '1.0',
    'depends': ['mrp', 'account', 'stock_account'],
    'author': "Matt O'Bell Ltd.",
    'website': 'http://www.mattobell.com',
    'description': '''
More Features on Manufacturing
==============================================================
- Modules to add more costs accounts on workcenters and production loss features.
- Also show total cost of workcenters, total cost of raw materials and total cost of finish products on production form.
- User can create parent workcenter and divide the cost in percentage in child workcenters accordingly to capacity and efficiency.
..
..
    ''',
    'category': 'Manufacturing',
    'sequence': 32,
    'data': [
        'views/mrp_workcenter_view.xml',
        'views/mrp_bom_view.xml',
        'views/mrp_production_view.xml',
        'views/mrp_routing_view.xml',
        'views/manufacturing_order_view.xml',
        'views/stock_move_view.xml',
    ],
    'demo':[],
    'auto_install': False,
    'installable': True,
    'application': False,
}
