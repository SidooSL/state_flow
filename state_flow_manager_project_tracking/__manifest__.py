{
    'name': 'State Flow Tracking for Projects',
    'version': '18.0.1.0.0',
    'category': 'Services/Project',
    'summary': 'Integrates State Flow Tracking with Projects',
    'description': """
This module allows check project state tracking.
    """,
    'author': 'Sidoo',
    'website': 'https://sidoo.es',
    'license': 'AGPL-3',
    'depends': [
        'state_flow_manager_project',
        'state_flow_manager_tracking'
    ],
    'data': [
        'views/project_project_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
} 