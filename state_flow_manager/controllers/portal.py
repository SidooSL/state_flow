from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class StateFlowPortal(http.Controller):

    def _get_record_and_check_access(self, model_name, record_id, access_token=None):
        """ Utility to fetch record and check access for portal user. """
        try:
            model = request.env[model_name]
        except KeyError:
            return None # Model not found
        
        record_sudo = model.sudo().browse(record_id).exists()
        if not record_sudo:
            return None # Record not found

        # Standard portal access check if access_token is provided
        if access_token:
            try:
                record_sudo.check_access_token(access_token)
            except AccessError:
                return None # Invalid access token
        # If no token, rely on standard record rules for logged-in portal user
        # We might need to fetch the record as the current user to trigger access rule check
        # For now, let's assume if a user can see a page, they have read access.
        # The transition execution will further check rights.

        # Ensure the model is a state.flow.mixin instance
        if not isinstance(record_sudo.env.registry.get(model_name), type(request.env['state.flow.mixin'])):
             # More robust check: check if model inherits state.flow.mixin
            if not any(parent == 'state.flow.mixin' for parent in model._inherit_parents):
                return None # Not a state flow enabled model
        
        return record_sudo

    @http.route(['/my/record/<string:model_name>/<int:record_id>/transition'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_execute_transition(self, model_name, record_id, access_token=None, selected_transition_id=None, **kw):
        record_sudo = self._get_record_and_check_access(model_name, record_id, access_token=access_token)
        
        if not record_sudo:
            return request.render("portal.portal_error", {
                'error_message': _("The record you are trying to access does not exist, is not a state flow enabled model, or you do not have access.")
            })
        
        redirect_url = kw.get('redirect_url', record_sudo.get_portal_url() if hasattr(record_sudo, 'get_portal_url') else '/my')

        if not selected_transition_id:
            # This should ideally be handled by form validation on client side
            # but good to have a server-side check too.
            # Using a generic portal_error template for now, or could add a message to portal.portal_record_template
            return request.render("portal.portal_error", {
                'error_message': _("No transition was selected."),
                # 'record': record_sudo, # If using a template that can display the record context
            })

        try:
            transition_id = int(selected_transition_id)
            transition = request.env['state.flow.transition'].sudo().browse(transition_id)
            if not transition.exists():
                raise UserError(_("Invalid transition selected."))

            # Check if this transition is available for the current user on this record
            # We need to get the record in the context of the current (portal) user for this check
            record_as_user = record_sudo.with_user(request.env.user).with_context(record_sudo.env.context)
            
            if transition not in record_as_user.available_transition_ids:
                raise AccessError(_("You are not allowed to execute this transition or it is not available in the current state."))

            # Execute as the portal user
            record_as_user.selected_transition_id = transition_id
            record_as_user.execute_transition()
            
            # Optionally, add a success message for portal
            # request.session['state_flow_success_message'] = _("Transition '%s' executed successfully.") % transition.display_name

        except (AccessError, UserError) as e:
            # Store error message in session to display on the redirected page
            # This requires the target portal template to be ableto display such messages
            request.session['state_flow_error_message'] = str(e)
        except ValueError:
            request.session['state_flow_error_message'] = _("Invalid transition format.")
        except Exception as e:
            request.session['state_flow_error_message'] = _("An unexpected error occurred: %s") % str(e)
            # Log the full error for admin
            _logger = request.env['ir.logging']
            _logger.sudo().error(f"Portal Transition Execution Error: Model={model_name}, Record={record_id}, User={request.env.uid}, Error: {str(e)}")

        return request.redirect(redirect_url) 