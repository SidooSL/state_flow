from odoo import models, fields

class StateFlowState(models.Model):
    _name = 'state.flow.state'
    _description = 'State Flow State'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    icon_class = fields.Char(string="Icon CSS Class", help="CSS class for an icon to represent this state (e.g., 'fa-play-circle').")
    process_id = fields.Many2one('state.flow.process')
    sequence = fields.Integer(string='Sequence')
    out_transition_ids = fields.One2many('state.flow.transition', 'from_state_id', string='Outgoing Transitions')
    in_transition_ids = fields.One2many('state.flow.transition', 'to_state_id', string='Incoming Transitions')
    allow_change_process = fields.Boolean(string='Allow Change Process', default=False)

    # State-based Write Access Control
    allowed_write_group_ids = fields.Many2many(
        'res.groups', 
        'state_flow_state_write_res_groups_rel', 
        'state_id', 'group_id', 
        string='Allowed Write Groups',
        help="If set, only users in these groups can edit records in this state (in addition to standard access rights)."
    )
    allowed_write_user_ids = fields.Many2many(
        'res.users', 
        'state_flow_state_write_res_users_rel', 
        'state_id', 'user_id', 
        string='Allowed Write Users',
        help="If set, only these specific users can edit records in this state (in addition to standard access rights)."
    )
    write_access_code = fields.Text(
        string='Python Code for Write Access',
        groups='base.group_system',
        help='''Dynamic write access control via Python code.
                Executed if no groups/users are specified above or if they don\'t grant access.
                Context: 'record' (current business object), 'user' (current res.users object), 'env'.
                Code MUST return True if write is allowed, False otherwise.

                Example:
                - record.project_manager_id == user
                - user.has_group("project.group_project_manager") and record.amount_total < 1000

                WARNING: Security risk! Only for System Administrators.
                Ensure code is safe and returns a clear boolean.
             '''
    )
