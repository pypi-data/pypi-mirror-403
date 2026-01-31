import { d as defineComponent, H as watch, J as onMounted, x as onUnmounted, c as createElementBlock, a as createBaseVNode, t as toDisplayString, z as createVNode, B as withCtx, K as Fragment, L as renderList, C as createBlock, e as createCommentVNode, w as withModifiers, n as normalizeClass, a0 as normalizeStyle, A as unref, aC as ElIcon, aD as delete_default, r as ref, G as computed, D as resolveComponent, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "component-container" };
const _hoisted_2 = { class: "listbox-subtitle" };
const _hoisted_3 = {
  key: 0,
  class: "config-section"
};
const _hoisted_4 = {
  key: 0,
  class: "config-row"
};
const _hoisted_5 = { class: "column-type" };
const _hoisted_6 = {
  key: 1,
  class: "config-row"
};
const _hoisted_7 = { class: "column-type" };
const _hoisted_8 = { class: "column-list-wrapper" };
const _hoisted_9 = { class: "listbox" };
const _hoisted_10 = ["onClick", "onContextmenu"];
const _hoisted_11 = ["onClick"];
const _hoisted_12 = {
  key: 2,
  class: "table-wrapper"
};
const _hoisted_13 = { class: "styled-table" };
const _hoisted_14 = { class: "action-cell" };
const _hoisted_15 = {
  key: 3,
  class: "empty-state"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "ColumnActionInput",
  props: {
    schema: {
      type: Object,
      required: true
    },
    modelValue: {
      type: Object,
      default: () => ({
        rows: [],
        group_by_columns: [],
        order_by_column: null
      })
    },
    incomingColumns: {
      type: Array,
      default: () => []
    }
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const localValue = ref({
      rows: [],
      group_by_columns: [],
      order_by_column: null
    });
    const selectedColumns = ref([]);
    const showContextMenu = ref(false);
    const contextMenuPosition = ref({ x: 0, y: 0 });
    const contextMenuRef = ref(null);
    const firstSelectedIndex = ref(null);
    const allColumns = computed(() => props.incomingColumns);
    const filteredColumns = computed(() => {
      if (!props.schema.data_types || props.schema.data_types === "ALL") {
        return props.incomingColumns;
      }
      if (Array.isArray(props.schema.data_types)) {
        return props.incomingColumns.filter(
          (column) => props.schema.data_types.includes(column.data_type)
        );
      }
      return props.incomingColumns;
    });
    watch(
      () => props.modelValue,
      (newValue) => {
        if (newValue) {
          localValue.value = {
            rows: newValue.rows || [],
            group_by_columns: newValue.group_by_columns || [],
            order_by_column: newValue.order_by_column || null
          };
        }
      },
      { immediate: true, deep: true }
    );
    const emitUpdate = () => {
      emit("update:modelValue", { ...localValue.value });
    };
    const generateOutputName = (column, action) => {
      return props.schema.output_name_template.replace("{column}", column).replace("{action}", action);
    };
    const handleColumnClick = (clickedIndex, columnName, event) => {
      if (event.shiftKey && firstSelectedIndex.value !== null) {
        const start = Math.min(firstSelectedIndex.value, clickedIndex);
        const end = Math.max(firstSelectedIndex.value, clickedIndex);
        selectedColumns.value = filteredColumns.value.slice(start, end + 1).map((col) => col.name);
      } else {
        if (selectedColumns.value.length === 1 && selectedColumns.value[0] === columnName) {
          selectedColumns.value = [];
          firstSelectedIndex.value = null;
        } else {
          firstSelectedIndex.value = clickedIndex;
          selectedColumns.value = [columnName];
        }
      }
    };
    const openContextMenu = (columnName, event) => {
      event.preventDefault();
      if (!selectedColumns.value.includes(columnName)) {
        selectedColumns.value = [columnName];
      }
      contextMenuPosition.value = { x: event.clientX, y: event.clientY };
      showContextMenu.value = true;
    };
    const addRow = (action) => {
      selectedColumns.value.forEach((column) => {
        const newRow = {
          column,
          action,
          output_name: generateOutputName(column, action)
        };
        localValue.value.rows.push(newRow);
      });
      showContextMenu.value = false;
      selectedColumns.value = [];
      emitUpdate();
    };
    const removeRow = (index) => {
      localValue.value.rows.splice(index, 1);
      emitUpdate();
    };
    const updateOutputName = (index) => {
      const row = localValue.value.rows[index];
      row.output_name = generateOutputName(row.column, row.action);
      emitUpdate();
    };
    const handleClickOutside = (event) => {
      var _a;
      if (!((_a = contextMenuRef.value) == null ? void 0 : _a.contains(event.target))) {
        showContextMenu.value = false;
      }
    };
    onMounted(() => {
      window.addEventListener("click", handleClickOutside);
    });
    onUnmounted(() => {
      window.removeEventListener("click", handleClickOutside);
    });
    return (_ctx, _cache) => {
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      const _component_el_input = resolveComponent("el-input");
      const _component_el_button = resolveComponent("el-button");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("label", _hoisted_2, toDisplayString(__props.schema.label), 1),
        __props.schema.show_group_by || __props.schema.show_order_by ? (openBlock(), createElementBlock("div", _hoisted_3, [
          __props.schema.show_group_by ? (openBlock(), createElementBlock("div", _hoisted_4, [
            _cache[2] || (_cache[2] = createBaseVNode("label", { class: "config-label" }, "Group By (optional)", -1)),
            createVNode(_component_el_select, {
              modelValue: localValue.value.group_by_columns,
              "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => localValue.value.group_by_columns = $event),
              multiple: "",
              filterable: "",
              placeholder: "Select columns to group by...",
              style: { "width": "100%" },
              onChange: emitUpdate
            }, {
              default: withCtx(() => [
                (openBlock(true), createElementBlock(Fragment, null, renderList(allColumns.value, (column) => {
                  return openBlock(), createBlock(_component_el_option, {
                    key: column.name,
                    label: column.name,
                    value: column.name
                  }, {
                    default: withCtx(() => [
                      createBaseVNode("span", null, toDisplayString(column.name), 1),
                      createBaseVNode("span", _hoisted_5, toDisplayString(column.data_type), 1)
                    ]),
                    _: 2
                  }, 1032, ["label", "value"]);
                }), 128))
              ]),
              _: 1
            }, 8, ["modelValue"])
          ])) : createCommentVNode("", true),
          __props.schema.show_order_by ? (openBlock(), createElementBlock("div", _hoisted_6, [
            _cache[3] || (_cache[3] = createBaseVNode("label", { class: "config-label" }, "Order By (optional)", -1)),
            createVNode(_component_el_select, {
              modelValue: localValue.value.order_by_column,
              "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => localValue.value.order_by_column = $event),
              filterable: "",
              clearable: "",
              placeholder: "Select column to order by...",
              style: { "width": "100%" },
              onChange: emitUpdate
            }, {
              default: withCtx(() => [
                (openBlock(true), createElementBlock(Fragment, null, renderList(allColumns.value, (column) => {
                  return openBlock(), createBlock(_component_el_option, {
                    key: column.name,
                    label: column.name,
                    value: column.name
                  }, {
                    default: withCtx(() => [
                      createBaseVNode("span", null, toDisplayString(column.name), 1),
                      createBaseVNode("span", _hoisted_7, toDisplayString(column.data_type), 1)
                    ]),
                    _: 2
                  }, 1032, ["label", "value"]);
                }), 128))
              ]),
              _: 1
            }, 8, ["modelValue"])
          ])) : createCommentVNode("", true)
        ])) : createCommentVNode("", true),
        createBaseVNode("div", _hoisted_8, [
          _cache[4] || (_cache[4] = createBaseVNode("div", { class: "listbox-subtitle" }, "Available Columns", -1)),
          createBaseVNode("ul", _hoisted_9, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(filteredColumns.value, (column, index) => {
              return openBlock(), createElementBlock("li", {
                key: column.name,
                class: normalizeClass({ "is-selected": selectedColumns.value.includes(column.name) }),
                onClick: ($event) => handleColumnClick(index, column.name, $event),
                onContextmenu: withModifiers(($event) => openContextMenu(column.name, $event), ["prevent"])
              }, toDisplayString(column.name) + " (" + toDisplayString(column.data_type) + ") ", 43, _hoisted_10);
            }), 128))
          ])
        ]),
        showContextMenu.value ? (openBlock(), createElementBlock("div", {
          key: 1,
          ref_key: "contextMenuRef",
          ref: contextMenuRef,
          class: "context-menu",
          style: normalizeStyle({
            top: contextMenuPosition.value.y + "px",
            left: contextMenuPosition.value.x + "px"
          })
        }, [
          (openBlock(true), createElementBlock(Fragment, null, renderList(__props.schema.actions, (action) => {
            return openBlock(), createElementBlock("button", {
              key: action.value,
              onClick: ($event) => addRow(action.value)
            }, toDisplayString(action.label), 9, _hoisted_11);
          }), 128))
        ], 4)) : createCommentVNode("", true),
        _cache[7] || (_cache[7] = createBaseVNode("div", { class: "listbox-subtitle" }, "Settings", -1)),
        localValue.value.rows.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_12, [
          createBaseVNode("table", _hoisted_13, [
            _cache[5] || (_cache[5] = createBaseVNode("thead", null, [
              createBaseVNode("tr", null, [
                createBaseVNode("th", null, "Field"),
                createBaseVNode("th", null, "Action"),
                createBaseVNode("th", null, "Output Field Name"),
                createBaseVNode("th")
              ])
            ], -1)),
            createBaseVNode("tbody", null, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(localValue.value.rows, (row, index) => {
                return openBlock(), createElementBlock("tr", { key: index }, [
                  createBaseVNode("td", null, toDisplayString(row.column), 1),
                  createBaseVNode("td", null, [
                    createVNode(_component_el_select, {
                      modelValue: row.action,
                      "onUpdate:modelValue": ($event) => row.action = $event,
                      size: "small",
                      onChange: ($event) => updateOutputName(index)
                    }, {
                      default: withCtx(() => [
                        (openBlock(true), createElementBlock(Fragment, null, renderList(__props.schema.actions, (action) => {
                          return openBlock(), createBlock(_component_el_option, {
                            key: action.value,
                            label: action.label,
                            value: action.value
                          }, null, 8, ["label", "value"]);
                        }), 128))
                      ]),
                      _: 1
                    }, 8, ["modelValue", "onUpdate:modelValue", "onChange"])
                  ]),
                  createBaseVNode("td", null, [
                    createVNode(_component_el_input, {
                      modelValue: row.output_name,
                      "onUpdate:modelValue": ($event) => row.output_name = $event,
                      size: "small",
                      onChange: emitUpdate
                    }, null, 8, ["modelValue", "onUpdate:modelValue"])
                  ]),
                  createBaseVNode("td", _hoisted_14, [
                    createVNode(_component_el_button, {
                      type: "danger",
                      circle: "",
                      onClick: ($event) => removeRow(index)
                    }, {
                      default: withCtx(() => [
                        createVNode(unref(ElIcon), null, {
                          default: withCtx(() => [
                            createVNode(unref(delete_default))
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }, 8, ["onClick"])
                  ])
                ]);
              }), 128))
            ])
          ])
        ])) : (openBlock(), createElementBlock("div", _hoisted_15, [..._cache[6] || (_cache[6] = [
          createBaseVNode("p", null, "No rows configured.", -1),
          createBaseVNode("p", { class: "hint" }, "Right-click on a column above to add a row.", -1)
        ])]))
      ]);
    };
  }
});
const ColumnActionInput = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-d3070256"]]);
export {
  ColumnActionInput as default
};
