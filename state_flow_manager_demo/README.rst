========================
State Flow Manager Demo
========================

Overview
========

The State Flow Manager Demo module demonstrates how to add a state flow to the `res.partner` model in Odoo. It extends the functionality provided by the `state_flow_manager` module.

Modules
=======

state_flow_manager_demo
-----------------------

This module demonstrates the integration of state flow functionality with the `res.partner` model.

- **Models:**
  - `res_partner`: Inherits `res.partner` and adds state flow functionality.

- **Views:**
  - `res_partner_views.xml`: Views for managing state flow in `res.partner`.

Installation
============

1. Ensure that the `state_flow_manager` module is installed.
2. Install the `state_flow_manager_demo` module to see a demonstration of the state flow functionality.

Usage
=====

1. Navigate to the `res.partner` form view.
2. You will see the state flow fields and buttons integrated into the form.
3. Define a state flow process in the State Flow Process Manager.
4. Add states and transitions to the process.
5. Apply the state flow to `res.partner` records and manage their state transitions.

Licenses
========

This module is licensed under AGPL-3.0. Consult the `__manifest__.py` file for more details.