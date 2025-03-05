from odoo import models, fields

class StateFlowState(models.Model):
    _name = 'state.flow.state'
    _description = 'State Flow State'

    name = fields.Char(string='Name', required=True)
    process_id = fields.Many2one('state.flow.process')
    sequence = fields.Integer(string='Sequence')
    out_transition_ids = fields.One2many('state.flow.transition', 'from_state_id', string='Outgoing Transitions')
    in_transition_ids = fields.One2many('state.flow.transition', 'to_state_id', string='Incoming Transitions')
