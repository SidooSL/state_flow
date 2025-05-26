{
    'name': 'State Flow for Projects',
    'version': '18.0.1.0.0',
    'category': 'Services/Project',
    'summary': 'Integrates State Flow management with Projects',
    'description': """
This module allows managing project lifecycles using the State Flow system.
It adds state and transition management to the project form.
    """,
    'author': 'Sidoo',
    'website': 'https://sidoo.es',
    'license': 'AGPL-3',
    'depends': [
        'project',
        'state_flow_manager',
    ],
    'data': [
        'views/project_project_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
} 