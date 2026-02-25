from odoo import api, fields, models

class StateFlowMixin(models.AbstractModel):
    _inherit = 'state.flow.mixin'

    tracking_ids = fields.One2many(
        'state.flow.tracking', 'res_id', string='State Tracking',
        domain=lambda self: [('res_model', '=', self._name)],
        auto_join=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.current_state_id:
                self.env['state.flow.tracking'].create({
                    'state_id': record.current_state_id.id,
                    'res_model': record._name,
                    'res_id': record.id,
                    'start': fields.Datetime.now(),
                })
        return records

    def write(self, vals):
        if 'current_state_id' in vals:
            new_state_id = vals['current_state_id']
            for record in self:
                if record.current_state_id.id != new_state_id:
                    # End the current tracking record
                    current_tracking = self.env['state.flow.tracking'].search([
                        ('res_model', '=', record._name),
                        ('res_id', '=', record.id),
                        ('state_id', '=', record.current_state_id.id),
                        ('end', '=', False)
                    ], limit=1)
                    if current_tracking:
                        current_tracking.write({'end': fields.Datetime.now()})
                    
                    # Create new tracking record if we have a new state
                    if new_state_id:
                        self.env['state.flow.tracking'].create({
                            'state_id': new_state_id,
                            'res_model': record._name,
                            'res_id': record.id,
                            'start': fields.Datetime.now(),
                        })
        return super().write(vals)
