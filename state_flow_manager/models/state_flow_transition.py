from odoo import models, fields

class StateFlowTransition(models.Model):
    _name = 'state.flow.transition'
    _description = 'State Flow Transition'

    sequence = fields.Integer()
    name = fields.Char(required=True)
    description = fields.Text()
    process_id = fields.Many2one('state.flow.process', required=True)
    model_name_for_domain = fields.Char(related='process_id.model_id.model', store=True, string="Model Name for Domain")
    from_state_id = fields.Many2one('state.flow.state', string='From', required=True,
                                    domain="[('process_id', '=', process_id)]")
    to_state_id = fields.Many2one('state.flow.state', string='To', required=True,
                                  domain="[('process_id', '=', process_id)]")
    model_id = fields.Many2one('ir.model', string="Target Model", related='process_id.model_id')
    model_name = fields.Char(string="Target Model Technical Name", related='model_id.model')
    server_action_id = fields.Many2one('ir.actions.server', domain="[('model_id', '=', model_id)]")
    pre_condition_domain = fields.Char(string="Pre-condition Domain")
    domain_fail_message = fields.Text(string="Pre-condition Fail Message")
    allowed_group_ids = fields.Many2many('res.groups', string='Allowed Groups')
    allowed_user_ids = fields.Many2many('res.users', string='Allowed Specific Users')
    user_field_id = fields.Many2one(
        'ir.model.fields',
        string='User Field from Record (Single)',
        domain="[('model_id', '=', model_id), ('ttype', '=', 'many2one'), ('relation', '=', 'res.users')]",
        help="Select a single Many2one field on the record (e.g., Project Manager) whose user should be allowed. Checked if specific users are not set."
    )
    user_field_ids = fields.Many2many(
        'ir.model.fields',
        'state_flow_transition_ir_model_fields_rel', # Explicit relation table name
        'transition_id', 'field_id', # Column names
        string='User Fields from Record (Any Of)',
        domain="[('model_id', '=', model_id), ('ttype', '=', 'many2one'), ('relation', '=', 'res.users')]",
        help="Select one or more Many2one fields on the record. If the current user matches the user in ANY of these fields, they will be allowed. Checked after specific users and single user field."
    )
    allowed_users_code = fields.Text(
        string='Python Code for Allowed Users',
        groups='base.group_system',
        help='''Define allowed users via Python code.
                The code is executed with 'record' (the current business object),
                'env' (Odoo environment), and 'user' (current res.users object) in its context.
                It MUST return a res.users recordset or a list of user IDs.

                Examples:
                - record.user_id
                - env['res.users'].browse([1, 2, 3])
                - [u.id for u in record.some_one2many_field.mapped('user_field_on_related_model')]
                - record.company_id.user_ids  # (If applicable)

                If the code returns a res.users recordset, the current user must be in it.
                If it returns a list of IDs, the current user's ID must be in the list.

                WARNING: Executing arbitrary Python code has security implications.
                This field is only visible/editable by System Administrators.
                Ensure the code is safe, tested, and does not perform unintended operations.
                Invalid code or code that does not return the expected type will result in permission denial.
             '''
    )
    post_transition_domain = fields.Char(string="Post-condition Domain")
    post_transition_fail_message = fields.Text(string="Post-condition Fail Message")