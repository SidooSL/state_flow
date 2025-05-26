from odoo import models, fields

class ResPartner(models.Model):
    _inherit = ['res.partner', 'state.flow.mixin']
    _name = 'res.partner' # Explicitly set _name to ensure correct inheritance

    # The fields process_id, current_state_id, available_transition_ids, 
    # selected_transition_id are inherited from state.flow.mixin. 