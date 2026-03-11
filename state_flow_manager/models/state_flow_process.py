from odoo import api, models, fields, Command, _


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
    state_ids = fields.One2many('state.flow.state', 'process_id', string='States', copy=True)
    transition_ids = fields.One2many('state.flow.transition', 'process_id', string='Transitions', copy=True)
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
        """Override copy to correctly duplicate states and transitions.

        Odoo's default copy would clone transition records but keep their
        from_state_id / to_state_id pointing to the *original* states, causing
        those states to appear to own transitions from both processes.

        Strategy:
        1. Create the new process with empty state_ids and transition_ids so
           Odoo's default copy mechanism does not touch either of those lists.
        2. Copy each state manually, capturing the mapping
           {original_state_id: new_state_id} at creation time (100% reliable,
           no dependence on name/sequence uniqueness).
        3. Re-create each transition pointing to the new states via the map.
        """
        self.ensure_one()
        default = dict(default or {})
        default.setdefault('name', _("%s (copy)") % self.name)
        # Prevent Odoo from auto-copying both One2many lists
        default.setdefault('state_ids', [Command.clear()])
        default.setdefault('transition_ids', [Command.clear()])

        new_process = super().copy(default)

        # --- Step 1: copy states and build the ID map ---
        state_map = {}  # {old_state_id: new_state_id}
        for state in self.state_ids:
            new_state = state.copy({'process_id': new_process.id})
            state_map[state.id] = new_state.id

        # --- Step 2: re-create transitions with translated state references ---
        for transition in self.transition_ids:
            new_from = state_map.get(transition.from_state_id.id)
            new_to = state_map.get(transition.to_state_id.id)

            if not new_from or not new_to:
                # Guard: skip transitions whose states were not found in the map
                # (should never happen in a consistent dataset)
                continue

            self.env['state.flow.transition'].create({
                'sequence': transition.sequence,
                'name': transition.name,
                'description': transition.description,
                'process_id': new_process.id,
                'from_state_id': new_from,
                'to_state_id': new_to,
                'server_action_id': transition.server_action_id.id,
                'pre_condition_domain': transition.pre_condition_domain,
                'domain_fail_message': transition.domain_fail_message,
                'post_transition_domain': transition.post_transition_domain,
                'post_transition_fail_message': transition.post_transition_fail_message,
                'user_field_id': transition.user_field_id.id,
                'allowed_users_code': transition.sudo().allowed_users_code,
                'allowed_group_ids': [Command.set(transition.allowed_group_ids.ids)],
                'allowed_user_ids': [Command.set(transition.allowed_user_ids.ids)],
                'user_field_ids': [Command.set(transition.user_field_ids.ids)],
            })

        return new_process
    