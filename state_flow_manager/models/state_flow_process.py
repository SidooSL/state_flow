from odoo import api, models, fields


class StateFlowProcess(models.Model):
    _name = 'state.flow.process'
    _description = 'State Flow Process'

    # TODO: This is not working as expected.
    def _get_model_id_domain(self):
        # Find the ir.model record for 'state.flow.mixin'
        mixin_model = self.env['ir.model'].sudo().search([('model', '=', 'state.flow.mixin')], limit=1)
        if mixin_model:
            # Return domain for models that have 'state.flow.mixin' in their inheritance chain.
            # This means mixin_model.id will be in their 'inherited_model_ids' field.
            return [('inherited_model_ids', 'in', [mixin_model.id])]
        # Fallback if 'state.flow.mixin' model is not found for some reason (should not happen)
        return [('id', '=', False)]

    name = fields.Char(required=True)
    description = fields.Html(string='Description')
    state_ids = fields.One2many('state.flow.state', 'process_id', string='States')
    transition_ids = fields.One2many('state.flow.transition', 'process_id', string='Transitions')
    model_id = fields.Many2one(
        'ir.model', 
        string='Model', 
        required=True, 
        ondelete='cascade',
        domain=_get_model_id_domain # Referencing the method directly
    )
    model_name_for_domain = fields.Char(related='model_id.model', store=True, string="Model Name for Domain")
    domain = fields.Text()
    process_type = fields.Char()
    
    @api.model
    def get_process_graph_data(self, process_id, current_state_id=None):
        """ 
        Fetches states (nodes) and transitions (edges) for a given process_id.
        If current_state_id is provided, it marks that state in the output.
        This method is designed to be called via RPC from the JS widget.
        """
        process = self.browse(process_id)
        if not process.exists():
            return {'nodes': [], 'edges': []}

        nodes = []
        for state in process.state_ids:
            nodes.append({
                'id': state.id, # Actual ID of the state record
                'key': f'state_{state.id}', # Unique key for Mermaid
                'name': state.name,
                'is_current': state.id == current_state_id if current_state_id else False
            })

        edges = []
        for transition in process.transition_ids:
            if transition.from_state_id and transition.to_state_id:
                edges.append({
                    'id': transition.id,
                    'from': f'state_{transition.from_state_id.id}',
                    'to': f'state_{transition.to_state_id.id}',
                    'name': transition.name,
                })
        
        return {
            'nodes': nodes,
            'edges': edges
        }

    def action_open_web_diagram(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # Ensure the URL is correctly formed, especially if web.base.url might have a trailing slash
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        return {
            'type': 'ir.actions.act_url',
            'url': f'{base_url}/state_flow/process/{self.id}',
            'target': 'new',
        }


    def copy(self, default=None):
        # Manejar múltiples registros
        if len(self) > 1:
            result = self.env['state.flow.process']
            for record in self:
                result |= record.copy(default=default)
            return result
        
        # Logic for a single record
        self.ensure_one()
        default = dict(default or {})

        # If no name was provided, generate a "(copy)" or "(copy X)" suffix
        if not default.get('name'):
            base_name = self.name or ''
            
            # Look for existing copies of this process to determine if numbering is needed
            existing = self.env['state.flow.process'].search([
                ('name', 'ilike', f'{base_name} (copy')
            ])
            
            if not existing:
                default['name'] = f"{base_name} (copy)"
            else:

                counter = 1
                while True:
                    candidate_name = f"{base_name} (copy {counter})"
                    if not self.env['state.flow.process'].search([('name', '=', candidate_name)]):
                        default['name'] = candidate_name
                        break
                    counter += 1

        # Prevent ORM from auto-copying One2many children
        # We will manually copy states and transitions

        default['state_ids'] = False
        default['transition_ids'] = False

        # Create the new process without children
        new_process = super().copy(default=default)

        # Map old state IDs to new state IDs
        state_mapping = {}
        for old_state in self.state_ids:
            # Manually copy each state
            new_state_vals = {
                'name': old_state.name,
                'description': old_state.description,
                'icon_class': old_state.icon_class,
                'process_id': new_process.id,       #Assign to the new process
                'sequence': old_state.sequence,
                'allow_change_process': old_state.allow_change_process,
            }
            new_state = self.env['state.flow.state'].create(new_state_vals)
            state_mapping[old_state.id] = new_state.id

        # Copy transitions and remap from/to states using state_mapping
        for old_transition in self.transition_ids:
            new_from_state_id = state_mapping.get(old_transition.from_state_id.id)
            new_to_state_id = state_mapping.get(old_transition.to_state_id.id)

            # Only create the transition if both endpoints were successfully mapped
            if new_from_state_id and new_to_state_id:
                new_transition_vals = {
                    'sequence': old_transition.sequence,
                    'name': old_transition.name,
                    'description': old_transition.description,
                    'process_id': new_process.id,       # Assign to new process
                    'from_state_id': new_from_state_id,
                    'to_state_id': new_to_state_id,
                    'server_action_id': old_transition.server_action_id.id if old_transition.server_action_id else False,
                    'pre_condition_domain': old_transition.pre_condition_domain,
                    'domain_fail_message': old_transition.domain_fail_message,
                    
                    # M2M fields – copy by replacing the entire set
                    'allowed_group_ids': [(6, 0, old_transition.allowed_group_ids.ids)],
                    'allowed_user_ids': [(6, 0, old_transition.allowed_user_ids.ids)],
                    
                    # Many2one and Many2many user field configurations
                    'user_field_id': old_transition.user_field_id.id if old_transition.user_field_id else False,
                    'user_field_ids': [(6, 0, old_transition.user_field_ids.ids)],
                    
                    # Code / domain fields
                    'allowed_users_code': old_transition.allowed_users_code,
                    'post_transition_domain': old_transition.post_transition_domain,
                    'post_transition_fail_message': old_transition.post_transition_fail_message,
                }
                self.env['state.flow.transition'].create(new_transition_vals)

        return new_process
