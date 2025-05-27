from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
import logging
import json

_logger = logging.getLogger(__name__)

class StateFlowWebController(http.Controller):
    @http.route('/state_flow/state_info/<int:state_id>', type='http', auth='user')
    def state_flow_state_info(self, state_id, **kwargs):
        """Serves the webpage that displays a single state flow process diagram."""
        kwargs['show_actions'] = False
        kwargs['state_id'] = state_id
        State = request.env['state.flow.state']
        state = State.sudo().browse(state_id)
        if not state.exists():
            # Render a simple error if state not found, or let Odoo handle MissingError
            return request.make_response("State not found.", status=404)
        process_id = state.process_id.id if state.process_id else None
        if not process_id:
            # If state has no process, redirect to a generic error or list page
            return request.make_response("State does not belong to any process.", status=404)
        # Redirect to the process page
        return self.state_flow_process_page(process_id, **kwargs)

    @http.route('/state_flow/process_info/<int:process_id>', type='http', auth='user')
    def state_flow_process_info(self, process_id, **kwargs):
        """Serves the webpage that displays a single state flow process diagram."""
        kwargs['show_actions'] = False

        return self.state_flow_process_page(process_id, **kwargs)

    @http.route('/state_flow/process/<int:process_id>', type='http', auth='user')
    def state_flow_process_page(self, process_id, **kwargs):
        """Serves the webpage that displays a single state flow process diagram."""
        Process = request.env['state.flow.process']
        # Get show_actions from kwargs or context, default to True
        show_actions = kwargs.get('show_actions', request.context.get('show_actions', True))

        State = request.env['state.flow.state']
        state_id = kwargs.get('state_id')
    
        try:
            state = state_id and State.sudo().browse(int(state_id)) or False
            # Sudo to read process details for display, access rights checked before this.
            # Actual operations on process/state/transition will re-check rights.
            process = Process.sudo().browse(process_id)
            if not process.exists():
                # Render a simple error if process not found, or let Odoo handle MissingError
                return request.make_response("Process not found.", status=404)

            # Perform access check for the current user for the specific process record
            # This requires the user to have at least read access to the state.flow.process model
            # and for this specific record if record rules apply.
            can_read = False
            try:
                process.env[process._name].check_access('read')
                process.env[process._name].browse(process.id).check_access('read')
                can_read = True
            except (AccessError, MissingError):
                _logger.warning(f"User {request.env.uid} has no read access to process {process_id}", exc_info=True)
                # Fall through to generic error or AccessError handling by Odoo
                raise AccessError("You do not have permission to view this process.")

            if not can_read:
                 raise AccessError("You do not have permission to view this process.")

            process_data = Process.sudo().get_process_graph_data(process_id, current_state_id=None)
            return request.render('state_flow_manager.state_flow_web_diagram_page', {
                'process': process, # process is sudoed for display, actual ops need to re-check
                'process_data_json': process_data,
                'page_title': process.name,
                'show_actions': show_actions,  # Show actions like adding states/transitions
                'state': state,  # Current state if provided
            })
        except AccessError as e:
            _logger.error(f"Access denied for user {request.env.uid} to process {process_id}: {e}")
            # Let Odoo's default error handling for http routes manage AccessError
            # It usually shows a standard Odoo access error page.
            raise
        except MissingError as e:
            _logger.error(f"Missing resource for process {process_id}: {e}")
            # Let Odoo's default error handling for http routes manage MissingError
            raise
        except Exception as e:
            _logger.exception(f"Error rendering state flow process page for process {process_id}")
            # Generic error response
            return request.make_response("An unexpected error occurred while displaying the process. Please check server logs.", status=500)

    @http.route('/state_flow/process/<int:process_id>/add_state', type='http', auth='user', methods=['POST'], csrf=True)
    def add_state_to_process(self, process_id, **post):
        """Permite añadir un nuevo estado a un proceso desde la web."""
        Process = request.env['state.flow.process']
        State = request.env['state.flow.state']

        # Fetch process as current user to check access
        process = Process.browse(process_id)
        if not process.exists():
            request.session['state_flow_error_message'] = "Process not found."
            return request.redirect(f'/state_flow/process/{process_id}')
        try:
            # Check if the current user can write to this specific process record
            process.check_access_rights('write')
        except AccessError:
            request.session['state_flow_error_message'] = "You do not have permission to add states to this process."
            return request.redirect(f'/state_flow/process/{process_id}')

        name = post.get('state_name')
        sequence = int(post.get('state_sequence', 10))
        description = post.get('state_description', '')
        if not name:
            request.session['state_flow_error_message'] = "State name is required."
            return request.redirect(f'/state_flow/process/{process_id}')
        State.sudo().create({
            'name': name,
            'process_id': process.id,
            'sequence': sequence,
            'description': description,
        })
        request.session['state_flow_success_message'] = f"State '{name}' added successfully."
        return request.redirect(f'/state_flow/process/{process.id}')

    @http.route('/state_flow/process/<int:process_id>/add_state', type='http', auth='user', methods=['GET'], csrf=False)
    def add_state_to_process_get(self, process_id, **get):
        """Muestra un error amigable si se accede por GET a la ruta de añadir estado."""
        return request.make_response("This URL is only for submitting the add state form. Please return to the process page.", status=400)

    @http.route('/state_flow/process/<int:process_id>/add_transition', type='http', auth='user', methods=['POST'], csrf=True)
    def add_transition_to_process_form(self, process_id, **post):
        """Permite añadir una transición entre dos estados desde el formulario web."""
        Process = request.env['state.flow.process']
        State = request.env['state.flow.state']
        Transition = request.env['state.flow.transition']

        # Fetch process as current user to check access
        process = Process.browse(process_id)
        if not process.exists():
            request.session['state_flow_error_message'] = "Process not found."
            return request.redirect(f'/state_flow/process/{process_id}')
        try:
            # Check if the current user can write to this specific process record
            process.check_access_rights('write')
        except AccessError:
            request.session['state_flow_error_message'] = "You do not have permission to add transitions to this process."
            return request.redirect(f'/state_flow/process/{process_id}')

        from_state_id = post.get('from_state_id')
        to_state_id = post.get('to_state_id')
        transition_name = post.get('transition_name')
        if not transition_name:
            request.session['state_flow_error_message'] = "Transition name is required."
            return request.redirect(f'/state_flow/process/{process_id}')
        if not (from_state_id and to_state_id):
            request.session['state_flow_error_message'] = "Both origin and destination states are required."
            return request.redirect(f'/state_flow/process/{process_id}')
        if from_state_id == to_state_id:
            request.session['state_flow_error_message'] = "Origin and destination states must be different."
            return request.redirect(f'/state_flow/process/{process_id}')
        from_state = State.sudo().browse(int(from_state_id))
        to_state = State.sudo().browse(int(to_state_id))
        if not (from_state.exists() and to_state.exists()):
            request.session['state_flow_error_message'] = "Selected states do not exist."
            return request.redirect(f'/state_flow/process/{process_id}')
        # Check if transition already exists
        existing = Transition.sudo().search([
            ('process_id', '=', process.id),
            ('from_state_id', '=', from_state.id),
            ('to_state_id', '=', to_state.id)
        ], limit=1)
        if existing:
            request.session['state_flow_error_message'] = "A transition between these states already exists."
            return request.redirect(f'/state_flow/process/{process_id}')
        # Create transition
        Transition.sudo().create({
            'name': transition_name,
            'process_id': process.id,
            'from_state_id': from_state.id,
            'to_state_id': to_state.id,
            'sequence': 10,
        })
        request.session['state_flow_success_message'] = f"Transition '{transition_name}' added successfully."
        return request.redirect(f'/state_flow/process/{process_id}')

    @http.route('/state_flow/process/<int:process_id>/api/add_transition', type='json', auth='user', methods=['POST'], csrf=True)
    def add_transition_to_process(self, process_id, **post):
        """Crea una transición entre dos estados dados sus keys (state_<id>)."""
        try:
            data = request.jsonrequest
            from_key = data.get('from_key')
            to_key = data.get('to_key')
            if not (from_key and to_key and from_key.startswith('state_') and to_key.startswith('state_')):
                return { 'success': False, 'error': 'Datos inválidos.' }
            from_id = int(from_key.replace('state_', ''))
            to_id = int(to_key.replace('state_', ''))
            State = request.env['state.flow.state'].sudo()
            from_state = State.browse(from_id)
            to_state = State.browse(to_id)
            if not (from_state.exists() and to_state.exists()):
                return { 'success': False, 'error': 'Estado no encontrado.' }
            process = request.env['state.flow.process'].sudo().browse(process_id)
            if not process.exists():
                return { 'success': False, 'error': 'Proceso no encontrado.' }
            # Permiso mínimo: debe poder escribir en el proceso
            try:
                process.env[process._name].check_access('write')
            except AccessError:
                return { 'success': False, 'error': 'Sin permisos para modificar el proceso.' }
            # Crear transición
            request.env['state.flow.transition'].sudo().create({
                'name': f'Transición {from_state.name} → {to_state.name}',
                'process_id': process.id,
                'from_state_id': from_state.id,
                'to_state_id': to_state.id,
                'sequence': 10,
            })
            return { 'success': True }
        except Exception as e:
            return { 'success': False, 'error': str(e) }