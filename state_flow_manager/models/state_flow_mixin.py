from odoo import api, models, fields, _
from odoo.exceptions import UserError

class StateFlowMixin(models.AbstractModel):
    _name = 'state.flow.mixin'
    _description = 'State Flow Mixin'
    _inherit = ['mail.thread']
    
    available_process_ids = fields.Many2many('state.flow.process', 
        default=lambda self: self._default_available_process_ids(),)
    process_id = fields.Many2one(
        'state.flow.process',
        string='Process',    
        default=lambda self: self._default_process_id(),
    )
    current_state_id = fields.Many2one('state.flow.state', string='Current State',
                                       compute='_compute_current_state_id', store=True,
                                       tracking=True)
    available_transition_ids = fields.Many2many('state.flow.transition', compute='_compute_available_transitions')
    selected_transition_id = fields.Many2one('state.flow.transition', string='Transition',
                                             domain="[('id', 'in', available_transition_ids)]")

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

    @api.depends('current_state_id')
    def _compute_available_transitions(self):
        for record in self:
            record.available_transition_ids = record.current_state_id.out_transition_ids
    
    def execute_transition(self):
        transition = self.selected_transition_id
        if not transition:
            raise UserError(_('Please select a transition to execute'))
        domain = eval(transition.domain)
        if domain:
            domain.append(('id',
                           '=', self.id))
            domain_pass = self.env[self._name].search(domain)
            if not domain_pass:
                raise UserError(transition.domain_fail_message)
        self.current_state_id = transition.to_state_id
        server_action = transition.server_action_id
        if server_action:
            server_action.run()
        self.selected_transition_id = False
    

