from odoo import models, fields

class ProjectProject(models.Model):
    _inherit = ['project.project', 'state.flow.mixin']
    _name = 'project.project' # Explicitly set _name to ensure correct inheritance

    # The fields process_id, current_state_id, available_transition_ids, 
    # selected_transition_id are inherited from state.flow.mixin.
    # No additional fields are strictly necessary here unless you want to override
    # or add specific logic for project processes beyond what the mixin provides.

    # Example: If you wanted to set a default process specifically for projects,
    # you could override _default_process_id or _default_available_process_ids here.
    # For now, we'll rely on the mixin's default behavior or manual assignment.

    # Ensure that the model 'project.project' is passed correctly when the state flow diagram
    # widget is initialized if it relies on context or record data.
    # The state_flow_diagram_field_placeholder in the view will handle this. 