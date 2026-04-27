import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class StateFlowMixin(models.AbstractModel):
    _name = 'state.flow.mixin'
    _description = 'State Flow Mixin'
    _inherit = []
    
    available_process_ids = fields.Many2many('state.flow.process', 
        default=lambda self: self._default_available_process_ids(),)
    process_id = fields.Many2one(
        'state.flow.process',
        string='Process',    
        default=lambda self: self._default_process_id(),
        ondelete='restrict',
    )
    current_state_id = fields.Many2one('state.flow.state', string='Current State',
                                       compute='_compute_current_state_id', store=True,
                                       tracking=True)
    available_transition_ids = fields.Many2many('state.flow.transition', compute='_compute_available_transitions')
    available_transitions_ui_data = fields.Json(
        string="Available Transitions UI Data",
        compute='_compute_available_transitions_ui_data'
    )

    def _default_process_id(self):
        available_process_ids = self._default_available_process_ids()
        return available_process_ids and available_process_ids[0] or False
    
    def _default_available_process_ids(self):
        available_process_ids = self.env['state.flow.process'].search([('model_id.model', '=', self._name)])
        return available_process_ids
    
    @api.depends('process_id')
    def _compute_current_state_id(self):
        for record in self:
            record.current_state_id = record.process_id and record.process_id.state_ids and record.process_id.state_ids[0] or False

    @api.depends('current_state_id', 'process_id')
    def _compute_available_transitions(self):
        for record in self:
            if not record.current_state_id:
                record.available_transition_ids = False
                continue
            
            possible_transitions = record.current_state_id.out_transition_ids
            allowed_transitions_for_user = self.env['state.flow.transition']

            if not possible_transitions:
                record.available_transition_ids = False
                continue

            user_groups = self.env.user.groups_id
            current_user_id = self.env.context.get('uid') or self.env.user.id

            for transition in possible_transitions:
                can_execute = False
                # Check if any permission is set on the transition itself
                no_specific_permissions = not transition.allowed_group_ids and \
                                          not transition.allowed_user_ids and \
                                          not transition.user_field_id and \
                                          not transition.user_field_ids and \
                                          not transition.sudo().allowed_users_code
                
                if no_specific_permissions:
                    can_execute = True
                else:
                    # 1. Check allowed groups
                    if transition.allowed_group_ids and bool(transition.allowed_group_ids & user_groups):
                        can_execute = True
                    
                    # 2. Check allowed specific users
                    if not can_execute and transition.allowed_user_ids and current_user_id in transition.allowed_user_ids.ids:
                        can_execute = True
                    
                    # 3. Check user specified in the single user_field_id field
                    if not can_execute and transition.user_field_id and transition.user_field_id.sudo().name:
                        try:
                            field_name = transition.user_field_id.sudo().name
                            user_in_field = getattr(record, field_name)
                            if user_in_field and user_in_field.id == current_user_id:
                                can_execute = True
                        except AttributeError:
                            _logger.warning(
                                "AttributeError when checking single user_field_id for transition %s on record %s,%s. Field name: %s",
                                transition.id, record._name, record.id, transition.user_field_id.sudo().name,
                                exc_info=True
                            )
                            pass # Field not found or misconfigured, permission not granted by this rule

                    # 4. Check users specified in the multiple user_field_ids fields (Any Of)
                    if not can_execute and transition.user_field_ids:
                        for user_field_record in transition.user_field_ids:
                            if user_field_record and user_field_record.sudo().name:
                                try:
                                    field_name = user_field_record.sudo().name
                                    user_in_field = getattr(record, field_name)
                                    if user_in_field and user_in_field.id == current_user_id:
                                        can_execute = True
                                        break # Found a match, no need to check other fields in this set
                                except AttributeError:
                                    _logger.warning(
                                        "AttributeError when checking user_field_ids for transition %s on record %s,%s. Field name: %s",
                                        transition.id, record._name, record.id, user_field_record.sudo().name,
                                        exc_info=True
                                    )
                                    continue 
                    
                    # 5. Check Python code for allowed users
                    if not can_execute and transition.sudo().allowed_users_code:
                        eval_context = {
                            'env': self.env,
                            'record': record,
                            'user': self.env.user, # The current user as a recordset
                            'log': lambda message: _logger.info(f'AllowedUsersCode (T{transition.id}, R{record.id}): {message}'),
                            # Potentially add other safe utilities like datetime, dateutil if needed
                        }
                        try:
                            result = safe_eval(transition.sudo().allowed_users_code, eval_context)
                            if isinstance(result, models.BaseModel) and result._name == 'res.users': # Check if it's a res.users recordset
                                if current_user_id in result.ids:
                                    can_execute = True
                            elif isinstance(result, list) and all(isinstance(item, int) for item in result): # Check if it's a list of ints
                                if current_user_id in result:
                                    can_execute = True
                            else:
                                _logger.warning(
                                    "Python code for transition %s (record %s,%s) did not return a res.users recordset or a list of user IDs. Returned type: %s",
                                    transition.id, record._name, record.id, type(result)
                                )
                        except Exception as e:
                            _logger.error(
                                "Error executing Python code for transition %s (record %s,%s): %s",
                                transition.id, record._name, record.id, str(e),
                                exc_info=True
                            )
                            # Do not grant permission if code execution fails

                if can_execute:
                    allowed_transitions_for_user |= transition
            
            record.available_transition_ids = allowed_transitions_for_user
    
    def execute_transition(self, transition_id=None):
        self.ensure_one()

        if not transition_id:
            # Try to get transition_id from context if not passed (e.g. for old button actions)
            # However, for the new UI, transition_id should always be passed.
            transition_id = self.env.context.get('force_transition_id') # Example context key
            if not transition_id:
                raise UserError(_('No transition ID provided to execute.'))

        transition = self.env['state.flow.transition'].browse(transition_id)
        if not transition.exists():
            raise UserError(_('Transition with ID %s not found or you do not have access.') % transition_id)

        # Check if this transition is actually available for the current record and state
        if transition not in self.available_transition_ids:
            _logger.warning(
                f"User {self.env.user.login} (ID: {self.env.user.id}) "
                f"attempted to execute transition '{transition.name}' (ID: {transition.id}) "
                f"on record {self._name},{self.id} from state '{self.current_state_id.name}' (ID: {self.current_state_id.id}), "
                f"but this transition is not in the computed available_transition_ids. "
                f"Available: {self.available_transition_ids.ids}"
            )
            # Check permissions again for this specific transition for better error message
            # (This re-evaluates part of _compute_available_transitions for this one transition)
            can_execute_specific = False
            user_groups = self.env.user.groups_id
            current_user_id = self.env.user.id
            
            no_specific_permissions = not transition.allowed_group_ids and \
                                      not transition.allowed_user_ids and \
                                      not transition.user_field_id and \
                                      not transition.user_field_ids and \
                                      not transition.sudo().allowed_users_code
            if no_specific_permissions:
                can_execute_specific = True
            else:
                if transition.allowed_group_ids and bool(transition.allowed_group_ids & user_groups):
                    can_execute_specific = True
                
                if not can_execute_specific and transition.allowed_user_ids and current_user_id in transition.allowed_user_ids.ids:
                    can_execute_specific = True
                
                # Check user_field_id in execute_transition
                if not can_execute_specific and transition.user_field_id and transition.user_field_id.sudo().name:
                    field_name_on_self = transition.user_field_id.sudo().name
                    if hasattr(self, field_name_on_self):
                        user_in_field_on_self = getattr(self, field_name_on_self)
                        if user_in_field_on_self and user_in_field_on_self.id == current_user_id:
                            can_execute_specific = True
                
                # Note: For allowed_users_code and user_field_ids on transition,
                # the full check is complex and already performed in _compute_available_transitions.
                # Here, we are primarily concerned if the transition was grossly mis-selected or basic permissions fail.
                # If it passed _compute_available_transitions, complex code conditions were met.
            
            if not can_execute_specific:
                 raise UserError(_("You do not have the required permissions to execute transition '%s'.") % transition.name)
            elif transition.from_state_id != self.current_state_id:
                 raise UserError(_("Transition '%s' is not valid from the current state '%s'.") % (transition.name, self.current_state_id.name))
            else:
                 raise UserError(_("Transition '%s' is not currently available for this record.") % transition.name)

        # Store original state in case of post-condition failure
        original_state_id = self.current_state_id

        # Pre-condition domain check
        if transition.pre_condition_domain:
            try:
                domain = safe_eval(transition.pre_condition_domain)
            except Exception as e:
                raise UserError(_('Error evaluating pre-condition domain for transition %s: %s') % (transition.name, e))
            
            domain.append(('id', '=', self.id))
            if not self.env[self._name].search(domain):
                raise UserError(transition.domain_fail_message or 
                                _("The record does not meet the pre-conditions for transition '%s'.") % transition.name)

        # Execute server action before changing state
        server_action = transition.server_action_id
        if server_action:
            # It's important to run the action with the context of the current record
            server_action.sudo().with_context(active_model=self._name, active_id=self.id, active_ids=self.ids).run()
            # The standard run() should be sufficient if the action is configured correctly to use context.
            # server_action.run()

        # Change current state
        self.sudo().current_state_id = transition.to_state_id

        # Post-condition domain check
        if transition.post_transition_domain:
            try:
                post_domain = safe_eval(transition.post_transition_domain)
            except Exception as e:
                # Revert state if post-condition evaluation fails
                self.sudo().current_state_id = original_state_id
                raise UserError(_('Error evaluating post-condition domain for transition %s: %s') % (transition.name, e))

            post_domain.append(('id', '=', self.id))
            if not self.env[self._name].search(post_domain):
                # Revert state if post-condition fails
                self.sudo().current_state_id = original_state_id
                # Untrack the field to avoid logging the revert
                # self.env.context = dict(self.env.context)
                # self.env.context.pop('tracking_disable', None) # Ensure tracking is not disabled
                # self.with_context(tracking_disable=True).current_state_id = original_state_id
                # self.env['mail.thread']._message_track_post_commit() # Try to force commit of tracking
                raise UserError(transition.post_transition_fail_message or
                                _('The record does not meet the post-conditions after transition \'%s\'. State has been reverted.') % transition.name)

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """ Verifies that the operation is allowed for the current user according to state-based ACls.
            This is an additional layer on top of Odoo's standard access rights.
        """
        # First, perform standard Odoo access checks
        # If these fail, this method will raise an exception or return False, so we don't need to proceed further.
        super_can_access = super().check_access_rights(operation, raise_exception=False)
        if not super_can_access:
            if raise_exception:
                # Re-raise the exception with the original Odoo message if super failed
                # This is a bit tricky as super() already returned False. We rely on Odoo to have set up
                # the context for an AccessError if raise_exception=True was passed to it originally.
                # A more robust way would be to call super with raise_exception=True inside a try-except block
                # but that might double-evaluate or have side effects.
                # For now, let's assume if super_can_access is False, standard Odoo rules would deny.
                # We will construct a generic message if we can't get the specific one easily.
                # However, it's better to let the subsequent loop handle it if our rules also deny.
                # If our rules ALLOW, but super DENIED, we must still deny.
                # Let's re-evaluate super() with raise_exception=True only if our rules would pass
                # This logic is complex. For now, let standard Odoo access rights be the first gate.
                # If super().check_access_rights(operation, raise_exception=False) is False,
                # it means standard Odoo rules already forbid the operation.
                # We don't need to (and shouldn't) override that to grant access.
                # Our rules are an *additional* restriction layer.
                if raise_exception:
                     # Re-trigger super to get the original exception if possible
                    super().check_access_rights(operation, raise_exception=True)
                return False # Should have been raised by super already if raise_exception=True

        if operation == 'write' and self.ids: # Only apply to existing records for write
            # sudo() is used for reading state configuration, not for granting rights.
            # The check is for the current user (self.env.user).
            user_is_admin = self.env.user.has_group('base.group_system')
            current_user_id = self.env.user.id
            user_groups = self.env.user.groups_id

            for record in self.sudo(): # Iterate with sudo to read state config, actual record is record.env.context.get('active_id')? No, record is fine
                if not record.process_id or not record.current_state_id:
                    continue # No state flow process or state, skip state-based check for this record

                state = record.current_state_id
                state_allows_write = False

                # Check if any state-specific write permissions are defined
                has_state_specific_rules = state.allowed_write_group_ids or \
                                           state.allowed_write_user_ids or \
                                           state.write_access_code
                
                if not has_state_specific_rules:
                    state_allows_write = True # No specific rules for this state, so this layer allows
                else:
                    # 1. Check allowed write groups for the state
                    if state.allowed_write_group_ids and bool(state.allowed_write_group_ids & user_groups):
                        state_allows_write = True
                    
                    # 2. Check allowed write users for the state
                    if not state_allows_write and state.allowed_write_user_ids and current_user_id in state.allowed_write_user_ids.ids:
                        state_allows_write = True
                    
                    # 3. Check Python code for write access on the state
                    if not state_allows_write and state.write_access_code:
                        eval_context = {
                            'env': record.env, # Use record.env to ensure correct environment
                            'record': record,  # The actual record instance
                            'user': self.env.user, # The current user as a recordset
                            'log': lambda message: _logger.info(f'StateWriteAccessCode (S{state.id}, R{record.id}): {message}'),
                        }
                        try:
                            if safe_eval(state.write_access_code, eval_context):
                                state_allows_write = True
                        except Exception as e:
                            _logger.error(
                                "Error executing Python code for state write access (State %s, Record %s,%s): %s",
                                state.id, record._name, record.id, str(e),
                                exc_info=True
                            )
                            # Do not grant permission if code execution fails
                
                if not state_allows_write and not user_is_admin:
                    # If user is admin, they bypass this specific state-based check.
                    # Standard Odoo ACLs will still apply to admins.
                    if raise_exception:
                        message = _("You are not allowed to modify this record in its current state ('%(state_name)s') based on the state flow configuration.") % {
                            'state_name': state.name
                        }
                        raise AccessError(message)
                    return False
        
        # If we reached here, either operation wasn't 'write', or all state-based checks passed (or didn't apply).
        # And standard Odoo checks (super_can_access) also passed.
        return True # Must return True if super_can_access was True and our checks passed

    @api.depends('available_transition_ids')  # Or more precise dependencies of get_available_transitions_dict
    def _compute_available_transitions_ui_data(self):
        for record in self:
            if record.id and hasattr(record, 'get_available_transitions_dict'): # Ensure record is saved and method exists
                record.available_transitions_ui_data = record.get_available_transitions_dict()
            else:
                record.available_transitions_ui_data = []

    def get_available_transitions_dict(self):
        """
        Devuelve las transiciones disponibles como una lista de diccionarios {id, name} para el frontend.
        """
        self.ensure_one()
        return [
            {'id': t.id, 'name': t.name or f"Transition {t.id}"}
            for t in self.available_transition_ids
        ]


