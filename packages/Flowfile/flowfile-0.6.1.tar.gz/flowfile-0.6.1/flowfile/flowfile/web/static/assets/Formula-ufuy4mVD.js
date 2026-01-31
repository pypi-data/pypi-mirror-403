import { C as CodeLoader } from "./vue-content-loader.es-CMoRXo7N.js";
import { d as defineComponent, r as ref, H as watch, c as createElementBlock, t as toDisplayString, e as createCommentVNode, a as createBaseVNode, z as createVNode, o as openBlock, g as _export_sfc, l as useNodeStore, B as withCtx, A as unref, C as createBlock } from "./index-bcuE0Z0p.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import mainEditorRef from "./fullEditor-BVYnWm05.js";
import { C as ColumnSelector } from "./dropDown-D5YXaPRR.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
import "./PopOver-BHpt5rsj.js";
import "./vue-codemirror.esm-CwaYwln0.js";
const _hoisted_1$1 = {
  key: 0,
  class: "label"
};
const _hoisted_2$1 = { class: "select-wrapper" };
const _sfc_main$1 = /* @__PURE__ */ defineComponent({
  __name: "dropDownGeneric",
  props: {
    modelValue: {
      type: String,
      default: "NewField"
    },
    optionList: {
      type: Array,
      required: true
    },
    title: {
      type: String,
      default: ""
    },
    allowOther: {
      type: Boolean,
      default: true
    },
    placeholder: {
      type: String,
      default: "Select an option"
    },
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  emits: ["update:modelValue", "change"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const localSelectedValue = ref(props.modelValue);
    watch(
      () => props.modelValue,
      (newVal) => {
        localSelectedValue.value = newVal;
      }
    );
    watch(localSelectedValue, (newVal) => {
      emit("update:modelValue", newVal);
      emit("change", newVal);
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", null, [
        __props.title !== "" ? (openBlock(), createElementBlock("p", _hoisted_1$1, toDisplayString(__props.title), 1)) : createCommentVNode("", true),
        createBaseVNode("div", _hoisted_2$1, [
          createVNode(ColumnSelector, {
            modelValue: localSelectedValue.value,
            "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => localSelectedValue.value = $event),
            "column-options": __props.optionList,
            "allow-other": __props.allowOther,
            placeholder: __props.placeholder,
            "is-loading": __props.isLoading
          }, null, 8, ["modelValue", "column-options", "allow-other", "placeholder", "is-loading"])
        ])
      ]);
    };
  }
});
const DropDownGeneric = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["__scopeId", "data-v-11dc3ea7"]]);
const createFormulaInput = (field_name = "", data_type = "Auto", function_def = "") => {
  const fieldInput = {
    name: field_name,
    data_type
  };
  const functionInput = {
    field: fieldInput,
    function: function_def
  };
  return functionInput;
};
const createFormulaNode = (flowId = -1, nodeId = -1, pos_x = 0, pos_y = 0, field_name = "output_field", data_type = "Auto", function_def = "") => {
  const func_info = createFormulaInput(field_name, data_type, function_def);
  const nodeFunction = {
    flow_id: flowId,
    node_id: nodeId,
    pos_x,
    pos_y,
    function: func_info,
    cache_results: false
  };
  return nodeFunction;
};
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = { key: 0 };
const _hoisted_3 = {
  key: 0,
  class: "selector-container"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Formula",
  setup(__props, { expose: __expose }) {
    const showEditor = ref(false);
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const nodeFormula = ref(null);
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeFormula,
      onBeforeSave: () => {
        if (!nodeFormula.value || !formulaInput.value) {
          return false;
        }
        nodeFormula.value.function.function = nodeStore.inputCode;
        return true;
      }
    });
    const outputColumnSelector = ref({
      selectedValue: ""
    });
    const editorChild = ref(null);
    const formulaInput = ref(null);
    const dataTypes = [...nodeStore.getDataTypes(), "Auto"];
    const nodeData = ref(null);
    const loadNodeData = async (nodeId) => {
      var _a, _b;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      if (nodeData.value && nodeData.value.setting_input && nodeData.value.setting_input.is_setup) {
        nodeFormula.value = nodeData.value.setting_input;
        if (nodeFormula.value && nodeFormula.value.function) {
          formulaInput.value = nodeFormula.value.function;
          outputColumnSelector.value.selectedValue = formulaInput.value.field.name;
        }
      } else {
        nodeFormula.value = createFormulaNode(nodeStore.flow_id, nodeStore.node_id);
        nodeFormula.value.depending_on_id = (_b = (_a = nodeData.value) == null ? void 0 : _a.main_input) == null ? void 0 : _b.node_id;
        formulaInput.value = nodeFormula.value.function;
      }
      showEditor.value = true;
      dataLoaded.value = true;
    };
    __expose({ loadNodeData, pushNodeData, saveSettings });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodeFormula.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeFormula.value,
          "onUpdate:modelValue": [
            _cache[2] || (_cache[2] = ($event) => nodeFormula.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => {
            var _a, _b;
            return [
              unref(nodeStore).is_loaded ? (openBlock(), createElementBlock("div", _hoisted_2, [
                formulaInput.value && nodeFormula.value ? (openBlock(), createElementBlock("div", _hoisted_3, [
                  createVNode(DropDownGeneric, {
                    modelValue: formulaInput.value.field.name,
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => formulaInput.value.field.name = $event),
                    title: "Output field",
                    "allow-other": true,
                    "option-list": ((_b = (_a = nodeData.value) == null ? void 0 : _a.main_input) == null ? void 0 : _b.columns) ?? [],
                    placeholder: "Select or create field"
                  }, null, 8, ["modelValue", "option-list"]),
                  createVNode(DropDownGeneric, {
                    modelValue: formulaInput.value.field.data_type,
                    "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => formulaInput.value.field.data_type = $event),
                    "option-list": dataTypes,
                    title: "Data type",
                    "allow-other": false
                  }, null, 8, ["modelValue"])
                ])) : createCommentVNode("", true),
                showEditor.value && formulaInput.value ? (openBlock(), createBlock(mainEditorRef, {
                  key: 1,
                  ref_key: "editorChild",
                  ref: editorChild,
                  "editor-string": formulaInput.value.function
                }, null, 8, ["editor-string"])) : createCommentVNode("", true)
              ])) : createCommentVNode("", true)
            ];
          }),
          _: 1
        }, 8, ["modelValue", "onUpdate:modelValue", "onRequestSave"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const Formula = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-aca62cad"]]);
export {
  Formula as default
};
