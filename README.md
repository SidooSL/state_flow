# State Flow Manager

## Overview

The State Flow Manager module provides an abstract class to add a state flow to any Odoo model. It allows you to define processes, states, and transitions that can be applied to your models to manage their state transitions.

## Modules

### state_flow_manager

This module provides the core functionality for managing state flows.

- **Models:**
  - [`state_flow_mixin`](state_flow_manager/models/state_flow_mixin.py): Abstract model to add state flow functionality to any model.
  - [`state_flow_process`](state_flow_manager/models/state_flow_process.py): Model to define state flow processes.
  - [`state_flow_state`](state_flow_manager/models/state_flow_state.py): Model to define states within a process.
  - [`state_flow_transition`](state_flow_manager/models/state_flow_transition.py): Model to define transitions between states.

- **Views:**
  - [`state_flow_process_views.xml`](state_flow_manager/views/state_flow_process_views.xml): Views for managing state flow processes.

- **Security:**
  - [`ir.model.access.csv`](state_flow_manager/security/ir.model.access.csv): Access control rules for state flow models.

### state_flow_manager_demo

This module demonstrates how to add a state flow to the `res.partner` model.

- **Models:**
  - [`res_partner`](state_flow_manager_demo/models/res_partner.py): Inherits `res.partner` and adds state flow functionality.

- **Views:**
  - [`res_partner_views.xml`](state_flow_manager_demo/views/res_partner_views.xml): Views for managing state flow in `res.partner`.

## Installation

1. Clone the repository into your Odoo addons directory.
2. Update the Odoo module list.
3. Install the `state_flow_manager` module.
4. Install the `state_flow_manager_demo` module to see a demonstration of the state flow functionality.

## Usage

1. Define a state flow process in the State Flow Process Manager.
2. Add states and transitions to the process.
3. Apply the state flow mixin to your model to enable state flow functionality.

## Licenses
This repository is licensed under AGPL-3.0.

However, each module can have a totally different license. Consult each module's __manifest__.py file, which contains a license key that explains its license.

