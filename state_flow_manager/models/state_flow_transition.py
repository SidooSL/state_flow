from odoo import models, fields

class StateFlowTransition(models.Model):
    _name = 'state.flow.transition'
    _description = 'State Flow Transition'

    sequence = fields.Integer()
    name = fields.Char(required=True)
    process_id = fields.Many2one('state.flow.process', required=True)
    from_state_id = fields.Many2one('state.flow.state', string='From', required=True,
                                    domain="[('process_id', '=', process_id)]")
    to_state_id = fields.Many2one('state.flow.state', string='To', required=True,
                                  domain="[('process_id', '=', process_id)]")
    model_id = fields.Many2one('ir.model', related='process_id.model_id')
    model_name = fields.Char(related='model_id.model')
    server_action_id = fields.Many2one('ir.actions.server', domain="[('model_id', '=', model_id)]")
    domain = fields.Char()
    domain_fail_message = fields.Text()