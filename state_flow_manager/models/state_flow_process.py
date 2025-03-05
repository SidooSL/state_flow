from odoo import api, models, fields


class StateFlowProcess(models.Model):
    _name = 'state.flow.process'
    _description = 'State Flow Process'

    name = fields.Char(required=True)
    description = fields.Text()
    state_ids = fields.One2many('state.flow.state', 'process_id', string='States')
    transition_ids = fields.One2many('state.flow.transition', 'process_id', string='Transitions')
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    domain = fields.Text()
    process_type = fields.Char()
    

