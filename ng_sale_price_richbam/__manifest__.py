{
    'name': "Sales Price Margin On Product Categories",

    'description': """This module sets a category on the catefory of particular products such that when a percentage is set on the category, all 
    the products in the same category use the information on the price margin to compute their selling price by adding a percentage of the cost price 
    to the cost price.
    """,

    'summary': "Add sales price margin % to the product categories to determine the selling price of products within the said category",

    'author': "Matt O'Bell Ltd.",

    'website': "https://www.mattobell.com",

    'version': "1.0",

    'auto_install': False,

    'installable': True,

    'demo': [

    ],

    'depends': [
        'sale',
    ],

    'data': [
        'views/sale_price_margin.xml',
    ],
}