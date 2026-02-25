{
    'name': 'State Flow Manager Tracking',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Add tracking to State Flow Manager',
    'description': """
        This module adds tracking functionality to State Flow processes,
        recording the time spent in each state.
    """,
    'author': 'Sensedi',
    'website': 'https://sidoo.es',
    'license': 'AGPL-3',
    'depends': ['state_flow_manager'],
    'data': [
        'security/ir.model.access.csv',
        'views/state_flow_tracking_views.xml',
    ],
    'installable': True,
    'application': False,
}
