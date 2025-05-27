/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";
import { loadJS } from "@web/core/assets";

const { Component, useState, onWillUpdateProps, onMounted, onWillStart } = owl;

export class StateFlowManagerContainer extends Component {
    static template = "state_flow_manager.StateFlowManagerContainer";
    static props = {
        ...standardFieldProps, // We might not need all of these if not a typical field
        record: Object, // The current record object from the form view
        // reload_on_post: { type: Boolean, optional: true }, // If we need to read attributes from the tag
    };

    setup() {
        this.orm = useService("orm");
        this.notificationService = useService("notification");

        this.state = useState({
            processName: "",
            currentStateName: "",
            currentStateIcon: "",
            currentStateId: null, // This will hold the ID of the current state
            isLoading: true,
            availableTransitions: [],
        });

        // It's often better to ensure data processing happens after initial props are fully set.
        // onWillStart might be too early if record data isn't fully resolved.
        // onMounted is good for initial setup after the DOM element is ready.
        // onWillUpdateProps handles subsequent changes.

        onWillStart(async () => {
            // Font Awesome is usually already loaded by Odoo, but just in case
            try {
                await loadJS("/web/static/lib/fontawesome/css/font-awesome.css");
            } catch (error) {
                console.log("Font Awesome might already be loaded:", error);
            }
        });

        onMounted(async () => {
            console.log("SFMContainer: onMounted triggered.");
            await this._updateStateFlowData(this.props.record);
        });

        onWillUpdateProps(async (nextProps) => {
            console.log("SFMContainer: onWillUpdateProps triggered.");
            await this._updateStateFlowData(nextProps.record);
        });
    }

    // Helper to safely stringify for debug, avoiding circular issues for display
    _safeStringifyForDebug(obj) {
        if (obj === undefined) return "undefined";
        if (obj === null) return "null";
        try {
            // Attempt to stringify specific known parts if it's a complex field object
            if (obj && obj.records && Array.isArray(obj.records)) {
                return `Object with .records (count: ${obj.records.length}), first few IDs: ${obj.records.slice(0,3).map(r => r.data ? r.data.id : '?').join(', ')}`;
            }            
            if (Array.isArray(obj)) {
                 // For arrays of simple pairs or IDs
                if (obj.every(el => Array.isArray(el) && el.length <= 2 && (typeof el[0] === 'number' || typeof el[0] === 'string'))) {
                    return JSON.stringify(obj.slice(0, 5)); // Show first 5 items
                }
                return `Array (length: ${obj.length})`; 
            }
            if (typeof obj === 'object' && Object.keys(obj).length > 0) {
                 return `Object with keys: ${Object.keys(obj).join(", ")}`;
            }
            return String(obj); // Fallback for simple types or empty objects
        } catch (e) {
            return "Error stringifying object (likely circular)";
        }
    }

    async _updateStateFlowData(record) {
        console.log("SFMContainer: _updateStateFlowData called.");
        if (!record || !record.data) {
            console.log("SFMContainer: No record or record.data, setting isLoading false.");
            this.state.isLoading = false;
            return;
        }
        this.state.isLoading = true;
        // console.log("SFMContainer: record.data snapshot:", JSON.parse(JSON.stringify(record.data))); // REMOVED: Causes circular JSON error

        // Log specific fields of interest carefully
        console.log("SFMContainer: record.data.process_id:", record.data.process_id);
        console.log("SFMContainer: record.data.current_state_id:", record.data.current_state_id);
        // console.log("SFMContainer: Raw record.data.available_transition_ids:", record.data.available_transition_ids);

        const processData = record.data.process_id;
        this.state.processName = processData && processData.length > 1 ? processData[1] : _t("No Process Selected");

        const currentStateData = record.data.current_state_id;

        // Get the icon class for the current state if available
        if (currentStateData && currentStateData.length > 0) {
            try {
                const stateId = currentStateData[0];
                this.state.currentStateId = stateId;
                console.log("SFMContainer: Fetching icon_class for state ID:", stateId);
                const stateDetails = await this.orm.call(
                    'state.flow.state',
                    'read',
                    [stateId, ['icon_class', 'name']],
                    {}
                );
                console.log("SFMContainer: Got state details:", stateDetails);

                if (stateDetails && stateDetails.length > 0 && stateDetails[0].icon_class) {
                    this.state.currentStateName = stateDetails[0].name;
                }
                if (stateDetails && stateDetails.length > 0 && stateDetails[0].icon_class) {
                    let iconClass = stateDetails[0].icon_class.trim();
                    console.log("SFMContainer: Raw icon_class value:", iconClass);
                    
                    // Ensure the icon class has fa prefix
                    if (!iconClass.startsWith('fa ') && !iconClass.startsWith('fas ') && 
                        !iconClass.startsWith('far ') && !iconClass.startsWith('fab ')) {
                        if (iconClass.startsWith('fa-')) {
                            iconClass = 'fa ' + iconClass;
                        } else {
                            iconClass = 'fa fa-' + iconClass;
                        }
                    }
                    this.state.currentStateIcon = iconClass + ' me-2'; // Add margin for spacing
                    console.log("SFMContainer: Final icon class:", this.state.currentStateIcon);
                } else {
                    // Default icon if none is set
                    this.state.currentStateIcon = "fa fa-circle me-2";
                    console.log("SFMContainer: Using default icon (no icon_class found)");
                }
            } catch (error) {
                console.error("Error fetching state icon:", error);
                this.state.currentStateIcon = "fa fa-circle me-2"; // Default fallback
            }
        } else {
            this.state.currentStateIcon = "";
            console.log("SFMContainer: No current state, no icon set");
        }
        
        console.log("SFMContainer: Process Name set to:", this.state.processName);
        console.log("SFMContainer: Current State Name set to:", this.state.currentStateName);
        console.log("SFMContainer: Current State Icon set to:", this.state.currentStateIcon);
        console.log("SFMContainer: Current State Id set to:", this.state.currentStateId);
        console.log("SFMContainer: Available Transition IDs:", record.data.available_transition_ids);
        
        this.state.availableTransitions = []
        // get the currentIds from record.data.available_transition_ids
        const currentIds = record.data.available_transition_ids.currentIds;
        console.log("SFMContainer: Current IDs:", currentIds);
        // get the name of the transitions
        const transitionDetails = await this.orm.call(
            'state.flow.transition',
            'read',
            [currentIds, ['name']],
            {}
        );
        for (const transition of transitionDetails) {
            this.state.availableTransitions.push([
                transition.id,
                transition.name
            ]);
        } 

        // itera sobre record.data.available_transition_ids.records; y guarda en availableTransitions
        // const transitionDetails = await this.orm.call(
        //     'state.flow.transition',
        //     'read',
        //     [record.data.available_transition_ids.currentIds, ['name']],
        //     {}
        // );
        // for (const transition of transitionDetails) {
        //     this.state.availableTransitions.push([
        //         transition.id,
        //         transition.name
        //     ]);
        // }
        console.log("SFMContainer: Available Transitions set to:", this.state.availableTransitions);

        this.state.isLoading = false;
    }

    async executeTransition(transitionId) {
        if (!transitionId) {
            this.notificationService.add(_t("No valid transition ID provided."), { type: "warning" });
            return;
        }

        const record = this.props.record;
        if (!record || !record.resModel || !record.resId) {
            this.notificationService.add(_t("Record information is missing."), { type: "danger" });
            return;
        }

        try {
            this.state.isLoading = true;
            // The selected_transition_id field is removed from the model.
            // We now pass the transitionId directly to the orm.call.
            await this.orm.call(
                record.resModel, 
                "execute_transition", 
                [record.resId], // Positional arguments: list of IDs (just one here)
                { transition_id: transitionId } // Keyword arguments
            );
            await record.load(); 
            await this._updateStateFlowData(this.props.record); // Refresh component state
            this.notificationService.add(_t("Transition executed successfully."), { type: "success" });
        } catch (error) {
            console.error("Error executing transition:", error);
            const errorMessage = error.message?.data?.message || error.data?.message || _t("Unknown error occurred during transition.");
            this.notificationService.add(_t("Error: %s", errorMessage), { type: "danger" });
            // Attempt to reload record data even in case of error to reflect any partial server-side changes if applicable
            try {
                await record.load();
                await this._updateStateFlowData(this.props.record); // Refresh component state
            } catch (loadError) {
                console.error("Error reloading record data after transition error:", loadError);
                // If reloading fails, we might not be able to update the UI reliably here
            }
        } finally {
            this.state.isLoading = false;
        }
    }
}

// Register this component so it can be used as a widget
// The key "state_flow_manager_container" can be used in <field widget="state_flow_manager_container"/>
registry.category("fields").add("state_flow_manager_container", {
    component: StateFlowManagerContainer,
    // We can also define supported field types if necessary, e.g., for a dummy char field
    // supportedTypes: ["char"], 
}); 