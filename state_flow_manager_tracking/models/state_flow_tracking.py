from odoo import api, fields, models, _
from datetime import datetime

class StateFlowTracking(models.Model):
    _name = 'state.flow.tracking'
    _description = 'State Flow Tracking'
    _order = 'start desc'

    state_id = fields.Many2one('state.flow.state', string='State', required=True, ondelete='cascade')
    res_model = fields.Char(string='Related Model', required=True, index=True)
    res_id = fields.Many2oneReference(string='Related Record', model_field='res_model', required=True, index=True)
    
    start = fields.Datetime(string='Start Date', default=fields.Datetime.now, required=True)
    end = fields.Datetime(string='End Date')
    
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)
    duration_display = fields.Char(string='Duration', compute='_compute_duration', store=True)

    @api.depends('start', 'end')
    def _compute_duration(self):
        for record in self:
            if record.start and record.end:
                diff = record.end - record.start
                record.duration = diff.total_seconds() / 3600.0
                
                days = diff.days
                hours, remainder = divmod(diff.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                parts = []
                if days > 0:
                    parts.append(_('%d days') % days)
                if hours > 0:
                    parts.append(_('%d hours') % hours)
                if minutes > 0:
                    parts.append(_('%d minutes') % minutes)
                if not parts:
                    parts.append(_('%d seconds') % seconds)
                
                record.duration_display = ', '.join(parts)
            else:
                record.duration = 0.0
                record.duration_display = _('In progress...')
