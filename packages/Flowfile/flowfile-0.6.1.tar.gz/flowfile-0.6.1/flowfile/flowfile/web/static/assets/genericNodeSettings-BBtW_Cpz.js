import { d as defineComponent, l as useNodeStore, H as watch, r as ref, a5 as reactive, c as createElementBlock, z as createVNode, B as withCtx, T as renderSlot, a as createBaseVNode, f as createTextVNode, A as unref, aI as info_filled_default, n as normalizeClass, t as toDisplayString, e as createCommentVNode, K as Fragment, C as createBlock, aJ as d_caret_default, aD as delete_default, G as computed, D as resolveComponent, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "settings-wrapper" };
const _hoisted_2 = { class: "settings-section" };
const _hoisted_3 = { class: "setting-group" };
const _hoisted_4 = { class: "setting-header" };
const _hoisted_5 = { class: "setting-description-wrapper" };
const _hoisted_6 = { class: "setting-description" };
const _hoisted_7 = { class: "setting-group" };
const _hoisted_8 = { class: "setting-header" };
const _hoisted_9 = { class: "setting-description-wrapper" };
const _hoisted_10 = { class: "setting-description" };
const _hoisted_11 = {
  key: 0,
  class: "validation-error"
};
const _hoisted_12 = {
  key: 1,
  class: "validation-loading"
};
const _hoisted_13 = { class: "setting-group" };
const _hoisted_14 = { class: "settings-section" };
const _hoisted_15 = { class: "setting-group" };
const _hoisted_16 = { class: "setting-group" };
const _hoisted_17 = { class: "setting-group" };
const _hoisted_18 = { class: "setting-group" };
const _hoisted_19 = { class: "setting-header" };
const _hoisted_20 = { style: { "display": "flex", "gap": "0.5rem", "margin-top": "0.5rem" } };
const _hoisted_21 = {
  key: 0,
  class: "no-fields"
};
const _hoisted_22 = {
  key: 2,
  style: { "margin-top": "1rem" },
  class: "tip"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "genericNodeSettings",
  props: {
    modelValue: {}
  },
  emits: ["update:model-value", "request-save"],
  setup(__props, { emit: __emit }) {
    var _a, _b, _c, _d;
    const nodeStore = useNodeStore();
    const props = __props;
    const emit = __emit;
    const isLoadingSchema = ref(false);
    const activeTab = ref("main");
    const referenceError = ref(null);
    const isValidatingReference = ref(false);
    let validationTimeout = null;
    const defaultReference = computed(() => {
      var _a2;
      return `df_${((_a2 = props.modelValue) == null ? void 0 : _a2.node_id) ?? ""}`;
    });
    watch(activeTab, (newTab, oldTab) => {
      if (newTab === "output-schema" && oldTab !== "output-schema") {
        emit("request-save");
      }
    });
    const localSettings = ref({
      cache_results: ((_a = props.modelValue) == null ? void 0 : _a.cache_results) ?? false,
      description: ((_b = props.modelValue) == null ? void 0 : _b.description) ?? "",
      node_reference: ((_c = props.modelValue) == null ? void 0 : _c.node_reference) ?? ""
    });
    const outputFieldConfig = reactive(
      ((_d = props.modelValue) == null ? void 0 : _d.output_field_config) ?? {
        enabled: false,
        validation_mode_behavior: "select_only",
        fields: [],
        validate_data_types: false
      }
    );
    watch(
      () => props.modelValue,
      (newValue) => {
        if (newValue) {
          localSettings.value = {
            cache_results: newValue.cache_results,
            description: newValue.description ?? "",
            node_reference: newValue.node_reference ?? ""
          };
          if (newValue.output_field_config) {
            Object.assign(outputFieldConfig, newValue.output_field_config);
          }
        }
      },
      { deep: true }
    );
    const handleSettingChange = () => {
      emit("update:model-value", {
        ...props.modelValue,
        cache_results: localSettings.value.cache_results,
        description: localSettings.value.description,
        node_reference: localSettings.value.node_reference,
        output_field_config: outputFieldConfig.enabled ? outputFieldConfig : null
      });
    };
    const handleDescriptionChange = (value) => {
      nodeStore.updateNodeDescription(props.modelValue.node_id, value);
      handleSettingChange();
    };
    const validateReferenceLocally = (value) => {
      if (!value || value === "") {
        return null;
      }
      if (value !== value.toLowerCase()) {
        return "Reference must be lowercase";
      }
      if (/\s/.test(value)) {
        return "Reference cannot contain spaces";
      }
      if (!/^[a-z][a-z0-9_]*$/.test(value)) {
        return "Reference must start with a letter and contain only lowercase letters, numbers, and underscores";
      }
      return null;
    };
    const handleReferenceInput = (value) => {
      if (validationTimeout) {
        clearTimeout(validationTimeout);
      }
      const localError = validateReferenceLocally(value);
      if (localError) {
        referenceError.value = localError;
        return;
      }
      referenceError.value = null;
      if (value && value !== "") {
        isValidatingReference.value = true;
        validationTimeout = setTimeout(async () => {
          try {
            const result = await nodeStore.validateNodeReference(props.modelValue.node_id, value);
            if (!result.valid) {
              referenceError.value = result.error;
            } else {
              referenceError.value = null;
            }
          } catch (error) {
            console.error("Error validating reference:", error);
          } finally {
            isValidatingReference.value = false;
          }
        }, 300);
      }
    };
    const handleReferenceBlur = async () => {
      if (validationTimeout) {
        clearTimeout(validationTimeout);
      }
      const value = localSettings.value.node_reference || "";
      const localError = validateReferenceLocally(value);
      if (localError) {
        referenceError.value = localError;
        return;
      }
      if (value !== "") {
        isValidatingReference.value = true;
        try {
          const result = await nodeStore.validateNodeReference(props.modelValue.node_id, value);
          if (!result.valid) {
            referenceError.value = result.error;
            return;
          }
        } catch (error) {
          console.error("Error validating reference:", error);
          return;
        } finally {
          isValidatingReference.value = false;
        }
      }
      if (!referenceError.value) {
        try {
          await nodeStore.setNodeReference(props.modelValue.node_id, value);
          handleSettingChange();
        } catch (error) {
          referenceError.value = error.message || "Failed to save reference";
        }
      }
    };
    const handleOutputConfigChange = () => {
      handleSettingChange();
    };
    const hasSchema = computed(() => {
      return outputFieldConfig.fields.length > 0;
    });
    const addField = () => {
      outputFieldConfig.fields.push({
        name: "",
        data_type: "String",
        default_value: null
      });
      handleOutputConfigChange();
    };
    const removeField = (index) => {
      outputFieldConfig.fields.splice(index, 1);
      handleOutputConfigChange();
    };
    const loadFieldsFromSchema = async () => {
      var _a2;
      try {
        if (!props.modelValue || !props.modelValue.node_id) {
          console.error("Cannot load schema: Invalid or missing node data");
          return;
        }
        isLoadingSchema.value = true;
        const saveResult = emit("request-save");
        if (saveResult instanceof Promise) {
          await saveResult;
        }
        await new Promise((resolve) => setTimeout(resolve, 100));
        const nodeData = await nodeStore.getNodeData(props.modelValue.node_id, false);
        if ((_a2 = nodeData == null ? void 0 : nodeData.main_output) == null ? void 0 : _a2.table_schema) {
          outputFieldConfig.fields = nodeData.main_output.table_schema.map((col) => ({
            name: col.name,
            data_type: col.data_type,
            default_value: null
          }));
          handleOutputConfigChange();
        }
      } catch (error) {
        console.error("Error loading schema:", error);
      } finally {
        isLoadingSchema.value = false;
      }
    };
    return (_ctx, _cache) => {
      const _component_el_tab_pane = resolveComponent("el-tab-pane");
      const _component_el_icon = resolveComponent("el-icon");
      const _component_el_tooltip = resolveComponent("el-tooltip");
      const _component_el_switch = resolveComponent("el-switch");
      const _component_el_input = resolveComponent("el-input");
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      const _component_el_button = resolveComponent("el-button");
      const _component_el_table_column = resolveComponent("el-table-column");
      const _component_el_table = resolveComponent("el-table");
      const _component_el_tabs = resolveComponent("el-tabs");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(_component_el_tabs, {
          modelValue: activeTab.value,
          "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => activeTab.value = $event)
        }, {
          default: withCtx(() => [
            createVNode(_component_el_tab_pane, {
              label: "Main Settings",
              name: "main"
            }, {
              default: withCtx(() => [
                renderSlot(_ctx.$slots, "default", {}, void 0, true)
              ]),
              _: 3
            }),
            createVNode(_component_el_tab_pane, {
              label: "General Settings",
              name: "general"
            }, {
              default: withCtx(() => [
                createBaseVNode("div", _hoisted_2, [
                  createBaseVNode("div", _hoisted_3, [
                    createBaseVNode("div", _hoisted_4, [
                      _cache[8] || (_cache[8] = createBaseVNode("span", { class: "setting-title" }, "Cache Results", -1)),
                      createBaseVNode("div", _hoisted_5, [
                        createBaseVNode("span", _hoisted_6, [
                          _cache[7] || (_cache[7] = createTextVNode(" Store results on disk to speed up subsequent executions and verify results. ", -1)),
                          createVNode(_component_el_tooltip, {
                            effect: "dark",
                            content: "Caching is only active when the flow is executed in performance mode",
                            placement: "top"
                          }, {
                            default: withCtx(() => [
                              createVNode(_component_el_icon, { class: "info-icon" }, {
                                default: withCtx(() => [
                                  createVNode(unref(info_filled_default))
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          })
                        ])
                      ])
                    ]),
                    createVNode(_component_el_switch, {
                      modelValue: localSettings.value.cache_results,
                      "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => localSettings.value.cache_results = $event),
                      onChange: handleSettingChange
                    }, null, 8, ["modelValue"])
                  ]),
                  createBaseVNode("div", _hoisted_7, [
                    createBaseVNode("div", _hoisted_8, [
                      _cache[10] || (_cache[10] = createBaseVNode("span", { class: "setting-title" }, "Node Reference", -1)),
                      createBaseVNode("div", _hoisted_9, [
                        createBaseVNode("span", _hoisted_10, [
                          _cache[9] || (_cache[9] = createTextVNode(" A unique identifier used as the variable name in code generation. ", -1)),
                          createVNode(_component_el_tooltip, {
                            effect: "dark",
                            content: "Must be lowercase with no spaces. Leave empty to use the default (df_node_id)",
                            placement: "top"
                          }, {
                            default: withCtx(() => [
                              createVNode(_component_el_icon, { class: "info-icon" }, {
                                default: withCtx(() => [
                                  createVNode(unref(info_filled_default))
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          })
                        ])
                      ])
                    ]),
                    createVNode(_component_el_input, {
                      modelValue: localSettings.value.node_reference,
                      "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => localSettings.value.node_reference = $event),
                      placeholder: defaultReference.value,
                      class: normalizeClass({ "is-error": referenceError.value }),
                      onInput: handleReferenceInput,
                      onBlur: handleReferenceBlur
                    }, null, 8, ["modelValue", "placeholder", "class"]),
                    referenceError.value ? (openBlock(), createElementBlock("div", _hoisted_11, toDisplayString(referenceError.value), 1)) : isValidatingReference.value ? (openBlock(), createElementBlock("div", _hoisted_12, "Checking...")) : createCommentVNode("", true)
                  ]),
                  createBaseVNode("div", _hoisted_13, [
                    _cache[11] || (_cache[11] = createBaseVNode("div", { class: "setting-header" }, [
                      createBaseVNode("span", { class: "setting-title" }, "Node Description"),
                      createBaseVNode("span", { class: "setting-description" }, " Add a description to document this node's purpose ")
                    ], -1)),
                    createVNode(_component_el_input, {
                      modelValue: localSettings.value.description,
                      "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => localSettings.value.description = $event),
                      type: "textarea",
                      rows: 4,
                      placeholder: "Add a description for this node...",
                      onChange: handleDescriptionChange
                    }, null, 8, ["modelValue"])
                  ])
                ])
              ]),
              _: 1
            }),
            createVNode(_component_el_tab_pane, {
              label: "Schema Validator",
              name: "output-schema"
            }, {
              default: withCtx(() => [
                createBaseVNode("div", _hoisted_14, [
                  createBaseVNode("div", _hoisted_15, [
                    _cache[12] || (_cache[12] = createBaseVNode("div", { class: "setting-header" }, [
                      createBaseVNode("span", { class: "setting-title" }, "Enable Schema Validation"),
                      createBaseVNode("span", { class: "setting-description" }, " Guarantee data quality with automatic schema enforcement and validation ")
                    ], -1)),
                    createVNode(_component_el_switch, {
                      modelValue: outputFieldConfig.enabled,
                      "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => outputFieldConfig.enabled = $event),
                      onChange: handleOutputConfigChange
                    }, null, 8, ["modelValue"])
                  ]),
                  outputFieldConfig.enabled ? (openBlock(), createElementBlock(Fragment, { key: 0 }, [
                    createBaseVNode("div", _hoisted_16, [
                      _cache[13] || (_cache[13] = createBaseVNode("div", { class: "setting-header" }, [
                        createBaseVNode("span", { class: "setting-title" }, "Validation Mode"),
                        createBaseVNode("span", { class: "setting-description" }, " How to handle output fields ")
                      ], -1)),
                      createVNode(_component_el_select, {
                        modelValue: outputFieldConfig.validation_mode_behavior,
                        "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => outputFieldConfig.validation_mode_behavior = $event),
                        style: { "width": "100%" },
                        onChange: handleOutputConfigChange
                      }, {
                        default: withCtx(() => [
                          createVNode(_component_el_option, {
                            label: "Strict - Keep only defined fields",
                            value: "select_only"
                          }),
                          createVNode(_component_el_option, {
                            label: "Flexible - Add missing fields, remove extras",
                            value: "add_missing"
                          }),
                          createVNode(_component_el_option, {
                            label: "Permissive - Add missing fields, keep all extras",
                            value: "add_missing_keep_extra"
                          }),
                          createVNode(_component_el_option, {
                            label: "Validate - Error if any fields are missing",
                            value: "raise_on_missing"
                          })
                        ]),
                        _: 1
                      }, 8, ["modelValue"])
                    ]),
                    createBaseVNode("div", _hoisted_17, [
                      _cache[14] || (_cache[14] = createBaseVNode("div", { class: "setting-header" }, [
                        createBaseVNode("span", { class: "setting-title" }, "Type Checking"),
                        createBaseVNode("span", { class: "setting-description" }, " Enforce data type constraints and catch type mismatches at runtime ")
                      ], -1)),
                      createVNode(_component_el_switch, {
                        modelValue: outputFieldConfig.validate_data_types,
                        "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => outputFieldConfig.validate_data_types = $event),
                        onChange: handleOutputConfigChange
                      }, null, 8, ["modelValue"])
                    ]),
                    createBaseVNode("div", _hoisted_18, [
                      createBaseVNode("div", _hoisted_19, [
                        _cache[17] || (_cache[17] = createBaseVNode("span", { class: "setting-title" }, "Schema Definition", -1)),
                        createBaseVNode("div", _hoisted_20, [
                          createVNode(_component_el_button, {
                            size: "small",
                            disabled: hasSchema.value,
                            loading: isLoadingSchema.value,
                            onClick: loadFieldsFromSchema
                          }, {
                            default: withCtx(() => [..._cache[15] || (_cache[15] = [
                              createTextVNode(" Auto-Detect Schema ", -1)
                            ])]),
                            _: 1
                          }, 8, ["disabled", "loading"]),
                          createVNode(_component_el_button, {
                            size: "small",
                            type: "primary",
                            onClick: addField
                          }, {
                            default: withCtx(() => [..._cache[16] || (_cache[16] = [
                              createTextVNode(" Add Field ", -1)
                            ])]),
                            _: 1
                          })
                        ])
                      ]),
                      outputFieldConfig.fields.length === 0 ? (openBlock(), createElementBlock("div", _hoisted_21, [
                        isLoadingSchema.value ? (openBlock(), createElementBlock(Fragment, { key: 0 }, [
                          createTextVNode(" Detecting schema... ")
                        ], 64)) : (openBlock(), createElementBlock(Fragment, { key: 1 }, [
                          createTextVNode(' No schema defined yet. Click "Auto-Detect Schema" to import from upstream data or "Add Field" to define manually. ')
                        ], 64))
                      ])) : (openBlock(), createBlock(_component_el_table, {
                        key: 1,
                        data: outputFieldConfig.fields,
                        style: { "width": "100%", "margin-top": "1rem" },
                        size: "small"
                      }, {
                        default: withCtx(() => [
                          createVNode(_component_el_table_column, { width: "50" }, {
                            default: withCtx(() => [
                              createVNode(_component_el_icon, { style: { "cursor": "move" } }, {
                                default: withCtx(() => [
                                  createVNode(unref(d_caret_default))
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          }),
                          createVNode(_component_el_table_column, {
                            label: "Field Name",
                            prop: "name"
                          }, {
                            default: withCtx(({ row }) => [
                              createVNode(_component_el_input, {
                                modelValue: row.name,
                                "onUpdate:modelValue": ($event) => row.name = $event,
                                size: "small",
                                onChange: handleOutputConfigChange
                              }, null, 8, ["modelValue", "onUpdate:modelValue"])
                            ]),
                            _: 1
                          }),
                          createVNode(_component_el_table_column, {
                            label: "Data Type",
                            prop: "data_type",
                            width: "150"
                          }, {
                            default: withCtx(({ row }) => [
                              createVNode(_component_el_select, {
                                modelValue: row.data_type,
                                "onUpdate:modelValue": ($event) => row.data_type = $event,
                                size: "small",
                                onChange: handleOutputConfigChange
                              }, {
                                default: withCtx(() => [
                                  createVNode(_component_el_option, {
                                    label: "String",
                                    value: "String"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "Int64",
                                    value: "Int64"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "Int32",
                                    value: "Int32"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "Float64",
                                    value: "Float64"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "Float32",
                                    value: "Float32"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "Boolean",
                                    value: "Boolean"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "Date",
                                    value: "Date"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "Datetime",
                                    value: "Datetime"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "Time",
                                    value: "Time"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "List",
                                    value: "List"
                                  }),
                                  createVNode(_component_el_option, {
                                    label: "Decimal",
                                    value: "Decimal"
                                  })
                                ]),
                                _: 1
                              }, 8, ["modelValue", "onUpdate:modelValue"])
                            ]),
                            _: 1
                          }),
                          createVNode(_component_el_table_column, {
                            label: "Default Value",
                            prop: "default_value"
                          }, {
                            default: withCtx(({ row }) => [
                              createVNode(_component_el_input, {
                                modelValue: row.default_value,
                                "onUpdate:modelValue": ($event) => row.default_value = $event,
                                size: "small",
                                placeholder: "null",
                                onChange: handleOutputConfigChange
                              }, null, 8, ["modelValue", "onUpdate:modelValue"])
                            ]),
                            _: 1
                          }),
                          createVNode(_component_el_table_column, { width: "60" }, {
                            default: withCtx(({ $index }) => [
                              createVNode(_component_el_button, {
                                type: "danger",
                                size: "small",
                                text: "",
                                onClick: ($event) => removeField($index)
                              }, {
                                default: withCtx(() => [
                                  createVNode(_component_el_icon, null, {
                                    default: withCtx(() => [
                                      createVNode(unref(delete_default))
                                    ]),
                                    _: 1
                                  })
                                ]),
                                _: 1
                              }, 8, ["onClick"])
                            ]),
                            _: 1
                          })
                        ]),
                        _: 1
                      }, 8, ["data"])),
                      outputFieldConfig.fields.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_22, [..._cache[18] || (_cache[18] = [
                        createBaseVNode("strong", null, "Tip:", -1),
                        createTextVNode(" Default values are used when fields are missing from the input data. ", -1)
                      ])])) : createCommentVNode("", true)
                    ])
                  ], 64)) : createCommentVNode("", true)
                ])
              ]),
              _: 1
            })
          ]),
          _: 3
        }, 8, ["modelValue"])
      ]);
    };
  }
});
const GenericNodeSettings = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-cc35309a"]]);
export {
  GenericNodeSettings as G
};
