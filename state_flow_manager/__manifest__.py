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
    'depends': ['mail', 'web', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'security/state_flow_security.xml',
        'views/state_flow_process_views.xml',
        'views/state_flow_transition_views.xml',
        'views/state_flow_portal_templates.xml',
        'views/state_flow_web_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'state_flow_manager/static/src/js/state_flow_widget.js',
            'state_flow_manager/static/src/js/state_flow_manager_container.js',
            'state_flow_manager/static/src/xml/state_flow_templates.xml',
            'state_flow_manager/static/src/js/state_flow_web_page.js',
            'state_flow_manager/static/lib/mermaid/mermaid.min.js',
        ],
        'web.assets_frontend': [
            'state_flow_manager/static/src/js/state_flow_web_page.js',
            'state_flow_manager/static/lib/mermaid/mermaid.min.js',
        ],
    },
    'installable': True,
    'application': False,
}