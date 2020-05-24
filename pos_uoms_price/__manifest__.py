{
    'name': 'POS Product multi unit of measure',
    'sequence': 0,
    'version': '2.1.6',
    'author': 'TL Technology',
    'description': 'Allow define 1 product have multi unit of measure, on pos screen can sale multi unit measure',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'import/template.xml',
        'views/product_product.xml',
        'views/pos_order.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
    'price': '50',
    'website': 'http://posodoo.com',
    "currency": 'EUR',
    'images': ['static/description/icon.png'],
    'support': 'thanhchatvn@gmail.com'
}
