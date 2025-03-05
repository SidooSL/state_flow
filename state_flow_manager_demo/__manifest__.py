{
    'name': 'Res Partner State Flow',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Module to add a State Flow to Res Partner',
    'description': """
        This module provides an abstract class to add a State Flow to Res Partner.
    """,
    "website": "https://sidoo.es",
    "license": "AGPL-3",
    'depends': ['state_flow_manager'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
}