import { d as defineComponent, l as useNodeStore, J as onMounted, a1 as nextTick, c as createElementBlock, z as createVNode, B as withCtx, a as createBaseVNode, f as createTextVNode, e as createCommentVNode, h as withDirectives, v as vModelText, A as unref, C as createBlock, r as ref, G as computed, D as resolveComponent, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import { C as ColumnSelector } from "./dropDown-D5YXaPRR.js";
import { u as unavailableField } from "./UnavailableFields-Yf6XSqFB.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
import { C as CodeLoader } from "./vue-content-loader.es-CMoRXo7N.js";
import "./PopOver-BHpt5rsj.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = { class: "table" };
const _hoisted_3 = {
  key: 0,
  class: "selectors"
};
const _hoisted_4 = {
  key: 0,
  class: "error-msg"
};
const _hoisted_5 = { class: "row" };
const _hoisted_6 = { class: "input-wrapper" };
const _hoisted_7 = { class: "row" };
const _hoisted_8 = {
  key: 1,
  class: "row"
};
const _hoisted_9 = {
  key: 2,
  class: "row"
};
const _hoisted_10 = { class: "row" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "TextToRows",
  setup(__props, { expose: __expose }) {
    const containsVal = (arr, val) => {
      return arr.includes(val);
    };
    const result = ref(null);
    const nodeStore = useNodeStore();
    const isLoaded = ref(false);
    const nodeTextToRows = ref(null);
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeTextToRows
    });
    const hasInvalidFields = computed(() => {
      return false;
    });
    const getEmptySetup = () => {
      return {
        column_to_split: "",
        output_column_name: "",
        split_by_fixed_value: true,
        split_fixed_value: ",",
        split_by_column: ""
      };
    };
    const loadNodeData = async (nodeId) => {
      var _a, _b;
      result.value = await nodeStore.getNodeData(nodeId, false);
      nodeTextToRows.value = (_a = result.value) == null ? void 0 : _a.setting_input;
      if (nodeTextToRows.value) {
        if (!nodeTextToRows.value.is_setup && ((_b = result.value) == null ? void 0 : _b.main_input)) {
          nodeTextToRows.value.text_to_rows_input = getEmptySetup();
        }
      }
      isLoaded.value = true;
    };
    const handleChange = (newValue, type) => {
      var _a;
      if ((_a = nodeTextToRows.value) == null ? void 0 : _a.text_to_rows_input)
        if (type === "columnToSplit") {
          nodeTextToRows.value.text_to_rows_input.column_to_split = newValue;
        } else {
          nodeTextToRows.value.text_to_rows_input.split_by_column = newValue;
        }
    };
    __expose({
      loadNodeData,
      pushNodeData,
      saveSettings,
      hasInvalidFields
    });
    onMounted(async () => {
      await nextTick();
    });
    return (_ctx, _cache) => {
      const _component_el_row = resolveComponent("el-row");
      const _component_el_radio = resolveComponent("el-radio");
      const _component_el_radio_group = resolveComponent("el-radio-group");
      const _component_el_col = resolveComponent("el-col");
      return isLoaded.value && nodeTextToRows.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeTextToRows.value,
          "onUpdate:modelValue": [
            _cache[7] || (_cache[7] = ($event) => nodeTextToRows.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => {
            var _a, _b, _c;
            return [
              createBaseVNode("div", _hoisted_2, [
                ((_a = nodeTextToRows.value) == null ? void 0 : _a.text_to_rows_input) ? (openBlock(), createElementBlock("div", _hoisted_3, [
                  !containsVal(
                    ((_c = (_b = result.value) == null ? void 0 : _b.main_input) == null ? void 0 : _c.columns) ?? [],
                    nodeTextToRows.value.text_to_rows_input.column_to_split
                  ) ? (openBlock(), createElementBlock("div", _hoisted_4, [
                    createVNode(unavailableField, {
                      "tooltip-text": "Setup is not valid",
                      class: "error-icon"
                    }),
                    _cache[8] || (_cache[8] = createTextVNode(" Check the column you want to split ", -1))
                  ])) : createCommentVNode("", true),
                  createBaseVNode("div", _hoisted_5, [
                    createVNode(_component_el_row, null, {
                      default: withCtx(() => {
                        var _a2, _b2;
                        return [
                          createBaseVNode("div", _hoisted_6, [
                            _cache[9] || (_cache[9] = createBaseVNode("label", null, "Column to split", -1)),
                            createVNode(ColumnSelector, {
                              modelValue: nodeTextToRows.value.text_to_rows_input.column_to_split,
                              "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => nodeTextToRows.value.text_to_rows_input.column_to_split = $event),
                              "column-options": (_b2 = (_a2 = result.value) == null ? void 0 : _a2.main_input) == null ? void 0 : _b2.columns,
                              "onUpdate:value": _cache[1] || (_cache[1] = (value) => handleChange(value, "columnToSplit"))
                            }, null, 8, ["modelValue", "column-options"])
                          ])
                        ];
                      }),
                      _: 1
                    })
                  ]),
                  createBaseVNode("div", _hoisted_7, [
                    createVNode(_component_el_radio_group, {
                      modelValue: nodeTextToRows.value.text_to_rows_input.split_by_fixed_value,
                      "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => nodeTextToRows.value.text_to_rows_input.split_by_fixed_value = $event),
                      size: "large"
                    }, {
                      default: withCtx(() => [
                        createVNode(_component_el_radio, { label: true }, {
                          default: withCtx(() => [..._cache[10] || (_cache[10] = [
                            createTextVNode("Split by a fixed value", -1)
                          ])]),
                          _: 1
                        }),
                        createVNode(_component_el_radio, { label: false }, {
                          default: withCtx(() => [..._cache[11] || (_cache[11] = [
                            createTextVNode("Split by a column", -1)
                          ])]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }, 8, ["modelValue"])
                  ]),
                  nodeTextToRows.value.text_to_rows_input.split_by_fixed_value ? (openBlock(), createElementBlock("div", _hoisted_8, [
                    createVNode(_component_el_col, { span: 10 }, {
                      default: withCtx(() => [..._cache[12] || (_cache[12] = [
                        createBaseVNode("label", null, "Split by value", -1)
                      ])]),
                      _: 1
                    }),
                    createVNode(_component_el_col, { span: 8 }, {
                      default: withCtx(() => [
                        withDirectives(createBaseVNode("input", {
                          "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => nodeTextToRows.value.text_to_rows_input.split_fixed_value = $event),
                          type: "text",
                          placeholder: "Enter split value"
                        }, null, 512), [
                          [vModelText, nodeTextToRows.value.text_to_rows_input.split_fixed_value]
                        ])
                      ]),
                      _: 1
                    })
                  ])) : createCommentVNode("", true),
                  !nodeTextToRows.value.text_to_rows_input.split_by_fixed_value ? (openBlock(), createElementBlock("div", _hoisted_9, [
                    createVNode(_component_el_col, { span: 10 }, {
                      default: withCtx(() => [..._cache[13] || (_cache[13] = [
                        createBaseVNode("label", null, "Column that contains the value to split", -1)
                      ])]),
                      _: 1
                    }),
                    createVNode(_component_el_col, { span: 8 }, {
                      default: withCtx(() => {
                        var _a2, _b2;
                        return [
                          createVNode(ColumnSelector, {
                            modelValue: nodeTextToRows.value.text_to_rows_input.split_by_column,
                            "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => nodeTextToRows.value.text_to_rows_input.split_by_column = $event),
                            "column-options": (_b2 = (_a2 = result.value) == null ? void 0 : _a2.main_input) == null ? void 0 : _b2.columns,
                            "allow-other": false,
                            "onUpdate:value": _cache[5] || (_cache[5] = (value) => handleChange(value, "splitValueColumn"))
                          }, null, 8, ["modelValue", "column-options"])
                        ];
                      }),
                      _: 1
                    })
                  ])) : createCommentVNode("", true),
                  createBaseVNode("div", _hoisted_10, [
                    createVNode(_component_el_col, { span: 10 }, {
                      default: withCtx(() => [..._cache[14] || (_cache[14] = [
                        createBaseVNode("label", null, "Output column name", -1)
                      ])]),
                      _: 1
                    }),
                    createVNode(_component_el_col, { span: 8 }, {
                      default: withCtx(() => {
                        var _a2, _b2;
                        return [
                          createVNode(ColumnSelector, {
                            modelValue: nodeTextToRows.value.text_to_rows_input.output_column_name,
                            "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => nodeTextToRows.value.text_to_rows_input.output_column_name = $event),
                            "column-options": (_b2 = (_a2 = result.value) == null ? void 0 : _a2.main_input) == null ? void 0 : _b2.columns,
                            "allow-other": true,
                            placeholder: "Enter output column name"
                          }, null, 8, ["modelValue", "column-options"])
                        ];
                      }),
                      _: 1
                    })
                  ])
                ])) : createCommentVNode("", true)
              ])
            ];
          }),
          _: 1
        }, 8, ["modelValue", "onUpdate:modelValue", "onRequestSave"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const TextToRows = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-bda46eae"]]);
export {
  TextToRows as default
};
