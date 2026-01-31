import { r as ref, d as defineComponent, l as useNodeStore, H as watch, c as createElementBlock, z as createVNode, B as withCtx, a as createBaseVNode, f as createTextVNode, t as toDisplayString, n as normalizeClass, K as Fragment, L as renderList, h as withDirectives, v as vModelText, A as unref, C as createBlock, e as createCommentVNode, E as ElNotification, D as resolveComponent, G as computed, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
const createManualInput = (flowId = -1, nodeId = -1, pos_x = 0, pos_y = 0) => {
  const nodeManualInput = ref({
    flow_id: flowId,
    node_id: nodeId,
    pos_x,
    pos_y,
    cache_input: false,
    raw_data_format: { columns: [], data: [] },
    cache_results: false
    // Add the missing property 'cache_results'
  });
  return nodeManualInput;
};
const _hoisted_1 = { key: 0 };
const _hoisted_2 = { class: "settings-section" };
const _hoisted_3 = { class: "controls-section controls-top" };
const _hoisted_4 = { class: "button-group" };
const _hoisted_5 = { class: "table-info" };
const _hoisted_6 = { class: "info-badge" };
const _hoisted_7 = { class: "info-badge" };
const _hoisted_8 = { class: "table-container" };
const _hoisted_9 = { class: "modern-table" };
const _hoisted_10 = { class: "header-row" };
const _hoisted_11 = { class: "column-header" };
const _hoisted_12 = { class: "header-top" };
const _hoisted_13 = ["onUpdate:modelValue", "placeholder"];
const _hoisted_14 = ["onClick"];
const _hoisted_15 = { class: "header-type" };
const _hoisted_16 = { class: "row-number" };
const _hoisted_17 = ["onUpdate:modelValue", "onKeydown"];
const _hoisted_18 = { class: "row-actions" };
const _hoisted_19 = ["onClick"];
const _hoisted_20 = {
  key: 0,
  class: "raw-data-section"
};
const _hoisted_21 = { class: "raw-data-controls" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "ManualInput",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const nodeManualInput = ref(null);
    const columns = ref([]);
    const rows = ref([]);
    const showRawData = ref(false);
    const rawDataString = ref("");
    let nextColumnId = 1;
    let nextRowId = 1;
    const dataTypes = nodeStore.getDataTypes();
    const inferDataType = (values) => {
      const validValues = values.filter((v) => v !== null && v !== void 0 && v !== "");
      if (validValues.length === 0) {
        return "String";
      }
      const allBooleans = validValues.every(
        (v) => typeof v === "boolean" || v === "true" || v === "false"
      );
      if (allBooleans) {
        return "Boolean";
      }
      const allNumeric = validValues.every((v) => {
        if (typeof v === "number") return true;
        if (typeof v === "string") {
          const parsed = Number(v);
          return !isNaN(parsed) && v.trim() !== "";
        }
        return false;
      });
      if (allNumeric) {
        const allIntegers = validValues.every((v) => {
          const num = typeof v === "number" ? v : Number(v);
          return Number.isInteger(num);
        });
        return allIntegers ? "Int64" : "Float64";
      }
      return "String";
    };
    const rawData = computed(() => {
      return rows.value.map((row) => {
        const obj = {};
        for (const col of columns.value) {
          obj[col.name] = row.values[col.id];
        }
        return obj;
      });
    });
    const rawDataFormat = computed(() => {
      const formattedColumns = columns.value.map((col) => ({
        name: col.name,
        data_type: col.dataType || "String"
      }));
      const data = columns.value.map(
        (col) => rows.value.map((row) => row.values[col.id] || "")
      );
      return {
        columns: formattedColumns,
        data
      };
    });
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeManualInput,
      onBeforeSave: () => {
        if (nodeManualInput.value) {
          nodeManualInput.value.raw_data_format = rawDataFormat.value;
        }
        return true;
      }
    });
    const initializeEmptyTable = () => {
      rows.value = [{ id: 1, values: { 1: "" } }];
      columns.value = [{ id: 1, name: "Column 1", dataType: "String" }];
      nextColumnId = 2;
      nextRowId = 2;
    };
    const populateTableFromData = (data) => {
      rows.value = [];
      columns.value = [];
      if (data.length === 0) {
        return;
      }
      const columnNames = Object.keys(data[0]);
      const columnValues = {};
      columnNames.forEach((name) => {
        columnValues[name] = data.map((item) => item[name]);
      });
      columnNames.forEach((name, colIndex) => {
        const inferredType = inferDataType(columnValues[name]);
        columns.value.push({
          id: colIndex + 1,
          name,
          dataType: inferredType
        });
      });
      data.forEach((item, rowIndex) => {
        const row = { id: rowIndex + 1, values: {} };
        columnNames.forEach((key, colIndex) => {
          row.values[colIndex + 1] = String(item[key] ?? "");
        });
        rows.value.push(row);
      });
      nextColumnId = columns.value.length + 1;
      nextRowId = rows.value.length + 1;
    };
    const populateTableFromRawDataFormat = (rawDataFormat2) => {
      var _a;
      rows.value = [];
      columns.value = [];
      if (rawDataFormat2.columns) {
        rawDataFormat2.columns.forEach((col, index) => {
          columns.value.push({
            id: index + 1,
            name: col.name,
            dataType: col.data_type || "String"
          });
        });
      }
      const numRows = ((_a = rawDataFormat2.data[0]) == null ? void 0 : _a.length) || 0;
      for (let rowIndex = 0; rowIndex < numRows; rowIndex++) {
        const row = { id: rowIndex + 1, values: {} };
        rawDataFormat2.data.forEach((colData, colIndex) => {
          row.values[colIndex + 1] = String(colData[rowIndex] || "");
        });
        rows.value.push(row);
      }
      if (numRows === 0 && columns.value.length > 0) {
        const emptyRow = { id: 1, values: {} };
        columns.value.forEach((col) => {
          emptyRow.values[col.id] = "";
        });
        rows.value.push(emptyRow);
        nextRowId = 2;
      } else {
        nextRowId = numRows + 1;
      }
      nextColumnId = columns.value.length + 1;
    };
    const loadNodeData = async (nodeId) => {
      const nodeResult = await nodeStore.getNodeData(nodeId, false);
      if (nodeResult == null ? void 0 : nodeResult.setting_input) {
        nodeManualInput.value = nodeResult.setting_input;
        console.log("nodeManualInput.value from input", nodeManualInput.value);
        if (nodeResult.setting_input.raw_data_format && nodeResult.setting_input.raw_data_format.columns && nodeResult.setting_input.raw_data_format.data) {
          populateTableFromRawDataFormat(nodeResult.setting_input.raw_data_format);
        } else if (nodeResult.setting_input.raw_data) {
          populateTableFromData(nodeResult.setting_input.raw_data);
        } else {
          initializeEmptyTable();
        }
      } else {
        nodeManualInput.value = createManualInput(nodeStore.flow_id, nodeStore.node_id).value;
        console.log("nodeManualInput.value no data available", nodeManualInput.value);
        initializeEmptyTable();
      }
      rawDataString.value = JSON.stringify(rawData.value, null, 2);
      dataLoaded.value = true;
    };
    const addColumn = () => {
      columns.value.push({
        id: nextColumnId,
        name: `Column ${nextColumnId}`,
        dataType: "String"
      });
      nextColumnId++;
    };
    const addRow = () => {
      const newRow = { id: nextRowId, values: {} };
      columns.value.forEach((col) => {
        newRow.values[col.id] = "";
      });
      rows.value.push(newRow);
      nextRowId++;
    };
    const deleteColumn = (id) => {
      const index = columns.value.findIndex((col) => col.id === id);
      if (index !== -1) {
        columns.value.splice(index, 1);
        rows.value.forEach((row) => {
          delete row.values[id];
        });
      }
    };
    const deleteRow = (id) => {
      const index = rows.value.findIndex((row) => row.id === id);
      if (index !== -1) {
        rows.value.splice(index, 1);
      }
    };
    const toggleRawData = () => {
      showRawData.value = !showRawData.value;
    };
    const selectAll = (event) => {
      const target = event.target;
      target.select();
    };
    const handleCellKeydown = (event, row, col) => {
      if (event.key === "Tab" && !event.shiftKey) {
        const colIndex = columns.value.findIndex((c) => c.id === col.id);
        const rowIndex = rows.value.findIndex((r) => r.id === row.id);
        if (colIndex === columns.value.length - 1 && rowIndex === rows.value.length - 1) {
          event.preventDefault();
          addRow();
          setTimeout(() => {
            const newRowCells = document.querySelectorAll(".data-row:last-child .input-cell");
            if (newRowCells.length > 0) {
              newRowCells[0].focus();
            }
          }, 0);
        }
      }
    };
    const updateTableFromRawData = () => {
      try {
        const newData = JSON.parse(rawDataString.value);
        if (!Array.isArray(newData)) {
          ElNotification({
            title: "Error",
            message: "Data must be an array of objects",
            type: "error"
          });
          return;
        }
        populateTableFromData(newData);
        ElNotification({
          title: "Success",
          message: "Table updated successfully",
          type: "success"
        });
      } catch (error) {
        ElNotification({
          title: "Error",
          message: "Invalid JSON format. Please check your input.",
          type: "error"
        });
      }
    };
    watch(rawData, (newVal) => {
      rawDataString.value = JSON.stringify(newVal, null, 2);
    });
    __expose({
      loadNodeData,
      pushNodeData,
      saveSettings
    });
    return (_ctx, _cache) => {
      const _component_el_button = resolveComponent("el-button");
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      const _component_el_input = resolveComponent("el-input");
      const _component_el_collapse_transition = resolveComponent("el-collapse-transition");
      return dataLoaded.value && nodeManualInput.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeManualInput.value,
          "onUpdate:modelValue": [
            _cache[3] || (_cache[3] = ($event) => nodeManualInput.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => [
            createBaseVNode("div", _hoisted_2, [
              createBaseVNode("div", _hoisted_3, [
                createBaseVNode("div", _hoisted_4, [
                  createVNode(_component_el_button, {
                    type: "primary",
                    size: "small",
                    onClick: addColumn
                  }, {
                    icon: withCtx(() => [..._cache[4] || (_cache[4] = [
                      createBaseVNode("i", { class: "fas fa-plus" }, null, -1)
                    ])]),
                    default: withCtx(() => [
                      _cache[5] || (_cache[5] = createTextVNode(" Add Column ", -1))
                    ]),
                    _: 1
                  }),
                  createVNode(_component_el_button, {
                    type: "primary",
                    size: "small",
                    onClick: addRow
                  }, {
                    icon: withCtx(() => [..._cache[6] || (_cache[6] = [
                      createBaseVNode("i", { class: "fas fa-plus" }, null, -1)
                    ])]),
                    default: withCtx(() => [
                      _cache[7] || (_cache[7] = createTextVNode(" Add Row ", -1))
                    ]),
                    _: 1
                  }),
                  createVNode(_component_el_button, {
                    size: "small",
                    onClick: toggleRawData
                  }, {
                    icon: withCtx(() => [
                      createBaseVNode("i", {
                        class: normalizeClass(showRawData.value ? "fas fa-eye-slash" : "fas fa-code")
                      }, null, 2)
                    ]),
                    default: withCtx(() => [
                      createTextVNode(" " + toDisplayString(showRawData.value ? "Hide JSON" : "Edit JSON"), 1)
                    ]),
                    _: 1
                  })
                ]),
                createBaseVNode("div", _hoisted_5, [
                  createBaseVNode("span", _hoisted_6, toDisplayString(columns.value.length) + " columns", 1),
                  createBaseVNode("span", _hoisted_7, toDisplayString(rows.value.length) + " rows", 1)
                ])
              ]),
              createBaseVNode("div", _hoisted_8, [
                createBaseVNode("table", _hoisted_9, [
                  createBaseVNode("thead", null, [
                    createBaseVNode("tr", _hoisted_10, [
                      _cache[9] || (_cache[9] = createBaseVNode("th", { class: "row-number-header" }, "#", -1)),
                      (openBlock(true), createElementBlock(Fragment, null, renderList(columns.value, (col) => {
                        return openBlock(), createElementBlock("th", {
                          key: col.id,
                          class: "column-header-cell"
                        }, [
                          createBaseVNode("div", _hoisted_11, [
                            createBaseVNode("div", _hoisted_12, [
                              withDirectives(createBaseVNode("input", {
                                "onUpdate:modelValue": ($event) => col.name = $event,
                                class: "input-header",
                                type: "text",
                                placeholder: `Column ${col.id}`,
                                onFocus: _cache[0] || (_cache[0] = ($event) => selectAll($event))
                              }, null, 40, _hoisted_13), [
                                [vModelText, col.name]
                              ]),
                              createBaseVNode("button", {
                                class: "delete-column-btn",
                                title: "Delete column",
                                onClick: ($event) => deleteColumn(col.id)
                              }, [..._cache[8] || (_cache[8] = [
                                createBaseVNode("i", { class: "fas fa-times" }, null, -1)
                              ])], 8, _hoisted_14)
                            ]),
                            createBaseVNode("div", _hoisted_15, [
                              createVNode(_component_el_select, {
                                modelValue: col.dataType,
                                "onUpdate:modelValue": ($event) => col.dataType = $event,
                                size: "small",
                                class: "type-select",
                                teleported: false
                              }, {
                                default: withCtx(() => [
                                  (openBlock(true), createElementBlock(Fragment, null, renderList(unref(dataTypes), (dtype) => {
                                    return openBlock(), createBlock(_component_el_option, {
                                      key: dtype,
                                      label: dtype,
                                      value: dtype
                                    }, null, 8, ["label", "value"]);
                                  }), 128))
                                ]),
                                _: 1
                              }, 8, ["modelValue", "onUpdate:modelValue"])
                            ])
                          ])
                        ]);
                      }), 128)),
                      _cache[10] || (_cache[10] = createBaseVNode("th", { class: "actions-header" }, null, -1))
                    ])
                  ]),
                  createBaseVNode("tbody", null, [
                    (openBlock(true), createElementBlock(Fragment, null, renderList(rows.value, (row, rowIndex) => {
                      return openBlock(), createElementBlock("tr", {
                        key: row.id,
                        class: "data-row"
                      }, [
                        createBaseVNode("td", _hoisted_16, toDisplayString(rowIndex + 1), 1),
                        (openBlock(true), createElementBlock(Fragment, null, renderList(columns.value, (col) => {
                          return openBlock(), createElementBlock("td", {
                            key: col.id,
                            class: "data-cell"
                          }, [
                            withDirectives(createBaseVNode("input", {
                              "onUpdate:modelValue": ($event) => row.values[col.id] = $event,
                              class: "input-cell",
                              type: "text",
                              onFocus: _cache[1] || (_cache[1] = ($event) => selectAll($event)),
                              onKeydown: ($event) => handleCellKeydown($event, row, col)
                            }, null, 40, _hoisted_17), [
                              [vModelText, row.values[col.id]]
                            ])
                          ]);
                        }), 128)),
                        createBaseVNode("td", _hoisted_18, [
                          createBaseVNode("button", {
                            class: "delete-row-btn",
                            title: "Delete row",
                            onClick: ($event) => deleteRow(row.id)
                          }, [..._cache[11] || (_cache[11] = [
                            createBaseVNode("i", { class: "fas fa-times" }, null, -1)
                          ])], 8, _hoisted_19)
                        ])
                      ]);
                    }), 128))
                  ])
                ])
              ]),
              createVNode(_component_el_collapse_transition, null, {
                default: withCtx(() => [
                  showRawData.value ? (openBlock(), createElementBlock("div", _hoisted_20, [
                    _cache[14] || (_cache[14] = createBaseVNode("div", { class: "raw-data-header" }, [
                      createBaseVNode("span", { class: "raw-data-title" }, "JSON Editor"),
                      createBaseVNode("span", { class: "raw-data-hint" }, "Edit the data as JSON array")
                    ], -1)),
                    createVNode(_component_el_input, {
                      modelValue: rawDataString.value,
                      "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => rawDataString.value = $event),
                      type: "textarea",
                      rows: 10,
                      placeholder: JSON.stringify([{ column1: "value1" }], null, 2),
                      class: "json-editor"
                    }, null, 8, ["modelValue", "placeholder"]),
                    createBaseVNode("div", _hoisted_21, [
                      createVNode(_component_el_button, {
                        type: "primary",
                        size: "small",
                        onClick: updateTableFromRawData
                      }, {
                        icon: withCtx(() => [..._cache[12] || (_cache[12] = [
                          createBaseVNode("i", { class: "fas fa-sync" }, null, -1)
                        ])]),
                        default: withCtx(() => [
                          _cache[13] || (_cache[13] = createTextVNode(" Apply JSON to Table ", -1))
                        ]),
                        _: 1
                      })
                    ])
                  ])) : createCommentVNode("", true)
                ]),
                _: 1
              })
            ])
          ]),
          _: 1
        }, 8, ["modelValue", "onUpdate:modelValue", "onRequestSave"])
      ])) : createCommentVNode("", true);
    };
  }
});
const ManualInput = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-4d8895ff"]]);
export {
  ManualInput as default
};
