{
    'name': 'State Flow for Case Files (Expedientes)',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Manages case files or general records with State Flow integration, including chatter and attachments.',
    'description': """
This module provides a model for managing 'Case Files' (Expedientes) 
that integrates with the State Flow system and includes features like 
chatter, activities, and attachments.
    """,
    'author': 'Sidoo',
    'website': 'https://sidoo.es',
    'license': 'AGPL-3',
    'depends': [
        'mail',  # For chatter, activities, attachments
        'state_flow_manager',
    ],
    'data': [
        'data/case_file_sequence.xml',
        'security/ir.model.access.csv',
        'views/case_file_views.xml',
    ],
    'installable': True,
    'application': True, # Can be a standalone application
    'auto_install': False,
} 