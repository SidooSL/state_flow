{
    'name': 'State Flow for Contacts',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Integrates State Flow management with Contacts (res.partner)',
    'description': """
This module allows managing contact/partner lifecycles using the State Flow system.
It adds state and transition management to the contact form.
    """,
    'author': 'Sidoo',
    'website': 'https://sidoo.es',
    'license': 'AGPL-3',
    'depends': [
        'contacts', # For res.partner form view and model
        'state_flow_manager',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
} 