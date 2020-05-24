{
    'name': "Invalidate cache",
    'author': "Matt O'Bell Ltd.",
    'description': """
Invalid Cache Do all
====================
Clear all caches at the same time from the list view,
This happens for all the pos sessions.
""",
    'summary': "Clean up the caches from tree view",
    'installable': True,
    'auto_install': False,
    'depends': [
      'point_of_sale',
    ],
    'data': [
        'views/pos_config_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
}
