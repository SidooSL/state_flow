from odoo import api, models, fields, _


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
        if len(self) > 1:
            return self.env['state.flow.process'].concat(*[r.copy(default) for r in self])
        
        self.ensure_one()
        default = dict(default or {})

        default['name'] = _("%s (copy)") % self.name

        default['state_ids'] = False
        default['transition_ids'] = False
        
        new = super().copy(default)
        state_map = {s.id: s.copy({'process_id': new.id}).id for s in self.state_ids}
        [t.copy({
            'process_id': new.id,
            'from_state_id': state_map[t.from_state_id.id],
            'to_state_id': state_map[t.to_state_id.id],
        }) for t in self.transition_ids]
        return new
    