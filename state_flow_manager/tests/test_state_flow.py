# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
# from .models import TestFlowModel # Removed: Model is now in main models directory
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import AccessError, UserError
from odoo import fields, api as new_api # Import new_api for environment refresh

_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install', 'state_flow')
class TestStateFlow(TransactionCase):
    """ Test suite for the State Flow Manager functionality. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Attempt a registry refresh for the current DB
        # This is to help ensure models from tests/models.py are loaded.
        # new_api.Environment.reset() # This might be too disruptive
        # cls.env.registry.clear_caches() # Clear registry caches
        # models.registry.Registry.new(cls.env.cr.dbname) # Rebuild registry - careful with this
        # Let's try a softer approach first - ensuring a fresh env for the lookup

        _logger.info("Setting up TestStateFlow class...")

        current_env = new_api.Environment(cls.env.cr, cls.env.uid, cls.env.context)

        cls.env = current_env # Use the newly created env for the class
        cls.ResUsers = cls.env['res.users']
        cls.StateFlowProcess = cls.env['state.flow.process']
        cls.StateFlowState = cls.env['state.flow.state']
        cls.StateFlowTransition = cls.env['state.flow.transition']
        cls.IrModel = cls.env['ir.model']

        cls.test_model_name = 'test.flow.model'
        _logger.info(f"Attempting to find test model: {cls.test_model_name}")
        
        # Model is now loaded as part of the main module, direct registry access should work.
        test_model_record = cls.IrModel._get(cls.test_model_name)
        
        if not test_model_record:
            _logger.error(f"Failed to find '{cls.test_model_name}' using IrModel._get(). Listing available models starting with 'test.flow':")
            test_models_found = cls.IrModel.search([('model', 'ilike', 'test.flow%')]) # ilike for broader search
            for m in test_models_found:
                _logger.error(f"Found via search: {m.model} (id: {m.id})")
            if cls.test_model_name not in cls.env:
                 _logger.error(f"'{cls.test_model_name}' also not found directly in env registry.")
            else:
                _logger.info(f"'{cls.test_model_name}' IS in env registry, ir.model._get issue? Ir.model record: {cls.env[cls.test_model_name]._name}")
            raise AssertionError(f"Test model '{cls.test_model_name}' not found in ir.model via _get. Ensure it is loaded and registered before tests run.")
        
        _logger.info(f"Found test model '{cls.test_model_name}' with ir.model ID: {test_model_record.id}")
        cls.test_model_id = test_model_record.id

        cls.group_sf_user = current_env.ref('state_flow_manager.group_state_flow_user', raise_if_not_found=False) 
        cls.group_sf_manager = current_env.ref('state_flow_manager.group_state_flow_manager', raise_if_not_found=False)
        
        if not cls.group_sf_user:
            cls.group_sf_user = current_env['res.groups'].create({'name': 'Test State Flow User Group'})
        if not cls.group_sf_manager:
            cls.group_sf_manager = current_env['res.groups'].create({'name': 'Test State Flow Manager Group'})

        cls.user_test_regular = cls.ResUsers.create({
            'name': 'Test Regular SF User',
            'login': 'test_regular_sf',
            'groups_id': [(6, 0, [cls.group_sf_user.id])]
        })
        cls.user_test_manager = cls.ResUsers.create({
            'name': 'Test Manager SF User',
            'login': 'test_manager_sf',
            'groups_id': [(6, 0, [cls.group_sf_user.id, cls.group_sf_manager.id])]
        })
        cls.user_test_other = cls.ResUsers.create({
            'name': 'Test Other SF User',
            'login': 'test_other_sf',
        })

        cls.process_test = cls.StateFlowProcess.create({
            'name': 'Test Document Process',
            'model_id': cls.test_model_id,
            'description': 'A simple process for testing purposes.'
        })

        cls.state_draft = cls.StateFlowState.create({
            'name': 'Draft',
            'process_id': cls.process_test.id,
            'sequence': 10,
        })
        cls.state_submitted = cls.StateFlowState.create({
            'name': 'Submitted',
            'process_id': cls.process_test.id,
            'sequence': 20,
        })
        cls.state_approved = cls.StateFlowState.create({
            'name': 'Approved',
            'process_id': cls.process_test.id,
            'sequence': 30,
        })
        cls.state_rejected = cls.StateFlowState.create({
            'name': 'Rejected',
            'process_id': cls.process_test.id,
            'sequence': 40,
        })

        cls.transition_draft_to_submit = cls.StateFlowTransition.create({
            'name': 'Submit Document',
            'process_id': cls.process_test.id,
            'from_state_id': cls.state_draft.id,
            'to_state_id': cls.state_submitted.id,
            'allowed_group_ids': [(6, 0, [cls.group_sf_user.id])]
        })
        cls.transition_submit_to_approve = cls.StateFlowTransition.create({
            'name': 'Approve Document',
            'process_id': cls.process_test.id,
            'from_state_id': cls.state_submitted.id,
            'to_state_id': cls.state_approved.id,
            'allowed_group_ids': [(6, 0, [cls.group_sf_manager.id])]
        })
        cls.transition_submit_to_reject = cls.StateFlowTransition.create({
            'name': 'Reject Document',
            'process_id': cls.process_test.id,
            'from_state_id': cls.state_submitted.id,
            'to_state_id': cls.state_rejected.id,
            'allowed_group_ids': [(6, 0, [cls.group_sf_manager.id])]
        })

        cls.TestModel = current_env[cls.test_model_name]
        cls.test_record = cls.TestModel.with_user(cls.user_test_regular).create({
            'name': 'Test Record Alpha',
            'process_id': cls.process_test.id,
        })
        _logger.info("TestStateFlow setUpClass completed.")

    def test_01_initial_state_assignment(self):
        self.assertEqual(self.test_record.current_state_id, self.state_draft, "Initial state should be Draft.")

    def test_02_available_transitions_regular_user_draft(self):
        record = self.test_record.with_user(self.user_test_regular)
        self.assertIn(self.transition_draft_to_submit, record.available_transition_ids, 
                        "Regular user should be able to 'Submit Document' from Draft.")
        self.assertNotIn(self.transition_submit_to_approve, record.available_transition_ids,
                         "Regular user should NOT see 'Approve Document' transition in Draft state.")

    def test_03_execute_transition_and_state_change(self):
        record = self.test_record.with_user(self.user_test_regular)
        record.selected_transition_id = self.transition_draft_to_submit
        record.execute_transition()
        self.assertEqual(record.current_state_id, self.state_submitted, "Record should now be in Submitted state.")

    def test_04_transition_permission_denied_wrong_group(self):
        record = self.TestModel.with_user(self.user_test_regular).create({
            'name': 'Test Record Beta for Permissions',
            'process_id': self.process_test.id,
        })
        self.assertEqual(record.current_state_id, self.state_draft, "Beta Record should start in Draft.")
        record_as_manager = record.with_user(self.user_test_manager)
        record_as_manager.selected_transition_id = self.transition_draft_to_submit
        record_as_manager.execute_transition()
        self.assertEqual(record.current_state_id, self.state_submitted, "Beta Record should be Submitted by manager.")

        record_as_regular = record.with_user(self.user_test_regular)
        self.assertNotIn(self.transition_submit_to_approve, record_as_regular.available_transition_ids,
                         "Regular user should NOT see 'Approve Document' in Submitted state.")
        self.assertNotIn(self.transition_submit_to_reject, record_as_regular.available_transition_ids,
                         "Regular user should NOT see 'Reject Document' in Submitted state.")

    def test_05_transition_permission_granted_correct_group(self):
        record = self.TestModel.with_user(self.user_test_manager).create({
            'name': 'Test Record Gamma for Permissions',
            'process_id': self.process_test.id,
        })
        record.selected_transition_id = self.transition_draft_to_submit
        record.execute_transition()
        self.assertEqual(record.current_state_id, self.state_submitted, "Gamma Record should be Submitted by manager.")

        self.assertIn(self.transition_submit_to_approve, record.available_transition_ids,
                      "Manager should see 'Approve Document' in Submitted state.")
        self.assertIn(self.transition_submit_to_reject, record.available_transition_ids,
                      "Manager should see 'Reject Document' in Submitted state.")

    # --- Start of Placeholder for More Tests ---
    # def test_06_transition_specific_user(self):
    #     pass
    # def test_07_transition_user_field_single(self):
    #     pass
    # def test_08_transition_user_field_multiple(self):
    #     pass
    # def test_09_transition_python_code_users(self):
    #     pass
    # def test_10_pre_condition_domain_fail(self):
    #     pass
    # def test_11_post_condition_domain_fail_rollback(self):
    #     pass
    # def test_12_write_access_state_groups(self):
    #     pass
    # def test_13_write_access_state_users(self):
    #     pass
    # def test_14_write_access_state_code(self):
    #     pass
    # def test_15_write_access_admin_override(self):
    #     pass
    # def test_16_no_permissions_on_transition(self):
    #     pass
    # def test_17_no_write_rules_on_state(self):
    #     pass 
    # --- End of Placeholder for More Tests ---


 