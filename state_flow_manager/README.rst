===================
State Flow Manager
===================

Overview
========

The State Flow Manager module provides an abstract class to add a state flow to any Odoo model. It allows you to define processes, states, and transitions that can be applied to your models to manage their state transitions.

Modules
=======

state_flow_manager
------------------

This module provides the core functionality for managing state flows.

- **Models:**
  - `state_flow_mixin`: Abstract model to add state flow functionality to any model.
  - `state_flow_process`: Model to define state flow processes.
  - `state_flow_state`: Model to define states within a process.
  - `state_flow_transition`: Model to define transitions between states.

- **Views:**
  - `state_flow_process_views.xml`: Views for managing state flow processes.

- **Security:**
  - `ir.model.access.csv`: Access control rules for state flow models.

Installation
============

1. Clone the repository:

`git clone <repository_url>`

2. Add the `state_flow_manager` module to your Odoo addons path.

3. Update the Odoo module list:

`./odoo-bin -u all`

4. Install the `state_flow_manager` module from the Odoo Apps menu.

Usage
=====

1. Define a state flow process in the State Flow Process Manager.
2. Add states and transitions to the process.
3. Apply the state flow to any model by inheriting the `state_flow_mixin` abstract model.
4. Manage state transitions for records of the model.

Licenses
========

This module is licensed under AGPL-3.0. Consult the `__manifest__.py` file for more details.