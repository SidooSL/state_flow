{
    'name': 'State Flow Manager',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Module to add a State Flow to any Odoo model',
    'description': """
        This module provides an abstract class to add a State Flow to any Odoo model.
    """,
    "website": "https://sidoo.es",
    "license": "AGPL-3",
    'depends': ['mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/state_flow_process_views.xml',
    ],
    'installable': True,
    'application': False,
}