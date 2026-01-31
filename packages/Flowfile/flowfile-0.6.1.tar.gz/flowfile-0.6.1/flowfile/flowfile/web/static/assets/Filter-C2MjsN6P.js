import { d as defineComponent, l as useNodeStore, c as createElementBlock, z as createVNode, B as withCtx, a as createBaseVNode, f as createTextVNode, e as createCommentVNode, A as unref, h as withDirectives, v as vModelText, t as toDisplayString, C as createBlock, r as ref, G as computed, D as resolveComponent, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
import { C as CodeLoader } from "./vue-content-loader.es-CMoRXo7N.js";
import { C as ColumnSelector } from "./dropDown-D5YXaPRR.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import mainEditorRef from "./fullEditor-BVYnWm05.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
import { F as FILTER_OPERATOR_LABELS, g as getFilterOperatorLabel, O as OPERATORS_WITH_VALUE2, a as OPERATORS_NO_VALUE } from "./node.types-Dl4gtSW9.js";
import "./PopOver-BHpt5rsj.js";
import "./vue-codemirror.esm-CwaYwln0.js";
const _hoisted_1 = { key: 0 };
const _hoisted_2 = { class: "listbox-wrapper" };
const _hoisted_3 = { style: { "border-radius": "20px" } };
const _hoisted_4 = { key: 0 };
const _hoisted_5 = { key: 1 };
const _hoisted_6 = { class: "filter-section" };
const _hoisted_7 = {
  key: 0,
  class: "filter-row"
};
const _hoisted_8 = { class: "filter-field" };
const _hoisted_9 = { class: "filter-field" };
const _hoisted_10 = {
  key: 0,
  class: "filter-field"
};
const _hoisted_11 = ["placeholder"];
const _hoisted_12 = {
  key: 1,
  class: "filter-field"
};
const _hoisted_13 = {
  key: 1,
  class: "help-text"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Filter",
  setup(__props, { expose: __expose }) {
    const editorString = ref("");
    const isLoaded = ref(false);
    const isAdvancedFilter = ref(false);
    const nodeStore = useNodeStore();
    const nodeFilter = ref(null);
    const nodeData = ref(null);
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeFilter,
      onBeforeSave: () => {
        if (nodeFilter.value) {
          if (isAdvancedFilter.value) {
            updateAdvancedFilter();
            nodeFilter.value.filter_input.mode = "advanced";
            nodeFilter.value.filter_input.filter_type = "advanced";
          } else {
            nodeFilter.value.filter_input.mode = "basic";
            nodeFilter.value.filter_input.filter_type = "basic";
          }
        }
        return true;
      }
    });
    const editorChild = ref(null);
    const operatorLabels = Object.keys(FILTER_OPERATOR_LABELS);
    const currentOperator = computed(() => {
      var _a, _b, _c;
      const op = (_c = (_b = (_a = nodeFilter.value) == null ? void 0 : _a.filter_input) == null ? void 0 : _b.basic_filter) == null ? void 0 : _c.operator;
      if (!op) return "equals";
      if (typeof op === "string") {
        if (Object.values(FILTER_OPERATOR_LABELS).includes(op)) {
          return op;
        }
        return convertLegacyOperator(op);
      }
      return op;
    });
    const operatorDisplayValue = computed({
      get: () => {
        var _a, _b, _c;
        return getOperatorLabel((_c = (_b = (_a = nodeFilter.value) == null ? void 0 : _a.filter_input) == null ? void 0 : _b.basic_filter) == null ? void 0 : _c.operator);
      },
      set: (val) => handleOperatorChange(val)
    });
    function convertLegacyOperator(symbol) {
      const legacyMapping = {
        "=": "equals",
        "==": "equals",
        "!=": "not_equals",
        "<>": "not_equals",
        ">": "greater_than",
        ">=": "greater_than_or_equals",
        "<": "less_than",
        "<=": "less_than_or_equals",
        contains: "contains",
        not_contains: "not_contains",
        starts_with: "starts_with",
        ends_with: "ends_with",
        is_null: "is_null",
        is_not_null: "is_not_null",
        in: "in",
        not_in: "not_in",
        between: "between",
        not_equals: "not_equals",
        greater_than: "greater_than",
        greater_than_or_equals: "greater_than_or_equals",
        less_than: "less_than",
        less_than_or_equals: "less_than_or_equals"
      };
      return legacyMapping[symbol] || "equals";
    }
    function getOperatorLabel(operator) {
      if (!operator) return "Equals";
      const op = typeof operator === "string" ? convertLegacyOperator(operator) : operator;
      return getFilterOperatorLabel(op);
    }
    const showValueInput = computed(() => {
      return !OPERATORS_NO_VALUE.includes(currentOperator.value);
    });
    const showValue2Input = computed(() => {
      return OPERATORS_WITH_VALUE2.includes(currentOperator.value);
    });
    const valuePlaceholder = computed(() => {
      switch (currentOperator.value) {
        case "in":
        case "not_in":
          return "value1, value2, value3";
        case "between":
          return "Start value";
        default:
          return "Enter value";
      }
    });
    const operatorHelpText = computed(() => {
      switch (currentOperator.value) {
        case "in":
        case "not_in":
          return "Enter comma-separated values";
        case "between":
          return "Enter the range boundaries (inclusive)";
        case "is_null":
          return "Filters rows where the column value is null";
        case "is_not_null":
          return "Filters rows where the column value is not null";
        default:
          return "";
      }
    });
    const handleFieldChange = (newValue) => {
      var _a;
      if ((_a = nodeFilter.value) == null ? void 0 : _a.filter_input.basic_filter) {
        nodeFilter.value.filter_input.basic_filter.field = newValue;
      }
    };
    const handleOperatorChange = (newLabel) => {
      var _a;
      if ((_a = nodeFilter.value) == null ? void 0 : _a.filter_input.basic_filter) {
        const operator = FILTER_OPERATOR_LABELS[newLabel];
        if (operator) {
          nodeFilter.value.filter_input.basic_filter.operator = operator;
          if (!OPERATORS_WITH_VALUE2.includes(operator)) {
            nodeFilter.value.filter_input.basic_filter.value2 = void 0;
          }
          if (OPERATORS_NO_VALUE.includes(operator)) {
            nodeFilter.value.filter_input.basic_filter.value = "";
          }
        }
      }
    };
    const loadNodeData = async (nodeId) => {
      var _a, _b, _c, _d, _e;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      if (nodeData.value) {
        nodeFilter.value = nodeData.value.setting_input;
        if ((_a = nodeFilter.value) == null ? void 0 : _a.filter_input.advanced_filter) {
          editorString.value = (_b = nodeFilter.value) == null ? void 0 : _b.filter_input.advanced_filter;
        }
        const mode = ((_c = nodeFilter.value) == null ? void 0 : _c.filter_input.mode) || ((_d = nodeFilter.value) == null ? void 0 : _d.filter_input.filter_type);
        isAdvancedFilter.value = mode === "advanced";
        if ((_e = nodeFilter.value) == null ? void 0 : _e.filter_input.basic_filter) {
          const bf = nodeFilter.value.filter_input.basic_filter;
          if (bf.filter_type && !bf.operator) {
            bf.operator = convertLegacyOperator(bf.filter_type);
          }
          if (bf.filter_value && !bf.value) {
            bf.value = bf.filter_value;
          }
          if (!bf.operator) {
            bf.operator = "equals";
          }
        }
      }
      isLoaded.value = true;
    };
    const updateAdvancedFilter = () => {
      if (nodeFilter.value) {
        nodeFilter.value.filter_input.advanced_filter = nodeStore.inputCode;
      }
    };
    __expose({ loadNodeData, pushNodeData, saveSettings });
    return (_ctx, _cache) => {
      const _component_el_switch = resolveComponent("el-switch");
      return isLoaded.value && nodeFilter.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeFilter.value,
          "onUpdate:modelValue": [
            _cache[7] || (_cache[7] = ($event) => nodeFilter.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => {
            var _a, _b, _c;
            return [
              createBaseVNode("div", _hoisted_2, [
                createBaseVNode("div", _hoisted_3, [
                  createVNode(_component_el_switch, {
                    modelValue: isAdvancedFilter.value,
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => isAdvancedFilter.value = $event),
                    class: "mb-2",
                    "active-text": "Advanced filter options",
                    "inactive-text": "Basic filter"
                  }, null, 8, ["modelValue"])
                ]),
                isAdvancedFilter.value ? (openBlock(), createElementBlock("div", _hoisted_4, [
                  _cache[8] || (_cache[8] = createTextVNode(" Advanced filter ", -1)),
                  createVNode(mainEditorRef, {
                    ref_key: "editorChild",
                    ref: editorChild,
                    "editor-string": editorString.value
                  }, null, 8, ["editor-string"])
                ])) : createCommentVNode("", true),
                !isAdvancedFilter.value ? (openBlock(), createElementBlock("div", _hoisted_5, [
                  createBaseVNode("div", _hoisted_6, [
                    ((_a = nodeFilter.value) == null ? void 0 : _a.filter_input.basic_filter) ? (openBlock(), createElementBlock("div", _hoisted_7, [
                      createBaseVNode("div", _hoisted_8, [
                        _cache[9] || (_cache[9] = createBaseVNode("label", { class: "filter-label" }, "Column", -1)),
                        createVNode(ColumnSelector, {
                          modelValue: nodeFilter.value.filter_input.basic_filter.field,
                          "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeFilter.value.filter_input.basic_filter.field = $event),
                          value: nodeFilter.value.filter_input.basic_filter.field,
                          "column-options": (_c = (_b = nodeData.value) == null ? void 0 : _b.main_input) == null ? void 0 : _c.columns,
                          "onUpdate:value": _cache[2] || (_cache[2] = (value) => handleFieldChange(value))
                        }, null, 8, ["modelValue", "value", "column-options"])
                      ]),
                      createBaseVNode("div", _hoisted_9, [
                        _cache[10] || (_cache[10] = createBaseVNode("label", { class: "filter-label" }, "Operator", -1)),
                        createVNode(ColumnSelector, {
                          modelValue: operatorDisplayValue.value,
                          "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => operatorDisplayValue.value = $event),
                          value: getOperatorLabel(nodeFilter.value.filter_input.basic_filter.operator),
                          "column-options": unref(operatorLabels),
                          "onUpdate:value": _cache[4] || (_cache[4] = (value) => handleOperatorChange(value))
                        }, null, 8, ["modelValue", "value", "column-options"])
                      ]),
                      showValueInput.value ? (openBlock(), createElementBlock("div", _hoisted_10, [
                        _cache[11] || (_cache[11] = createBaseVNode("label", { class: "filter-label" }, "Value", -1)),
                        withDirectives(createBaseVNode("input", {
                          "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => nodeFilter.value.filter_input.basic_filter.value = $event),
                          type: "text",
                          class: "input-field",
                          placeholder: valuePlaceholder.value
                        }, null, 8, _hoisted_11), [
                          [vModelText, nodeFilter.value.filter_input.basic_filter.value]
                        ])
                      ])) : createCommentVNode("", true),
                      showValue2Input.value ? (openBlock(), createElementBlock("div", _hoisted_12, [
                        _cache[12] || (_cache[12] = createBaseVNode("label", { class: "filter-label" }, "And", -1)),
                        withDirectives(createBaseVNode("input", {
                          "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => nodeFilter.value.filter_input.basic_filter.value2 = $event),
                          type: "text",
                          class: "input-field",
                          placeholder: "End value"
                        }, null, 512), [
                          [vModelText, nodeFilter.value.filter_input.basic_filter.value2]
                        ])
                      ])) : createCommentVNode("", true)
                    ])) : createCommentVNode("", true),
                    operatorHelpText.value ? (openBlock(), createElementBlock("div", _hoisted_13, toDisplayString(operatorHelpText.value), 1)) : createCommentVNode("", true)
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
const Filter = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-3a08b53d"]]);
export {
  Filter as default
};
