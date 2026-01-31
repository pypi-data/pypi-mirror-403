import { d as defineComponent, r as ref, H as watch, c as createElementBlock, a as createBaseVNode, z as createVNode, e as createCommentVNode, D as resolveComponent, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "excel-table-settings" };
const _hoisted_2 = { class: "mandatory-section" };
const _hoisted_3 = {
  key: 0,
  class: "section-divider"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "outputExcel",
  props: {
    modelValue: {
      type: Object,
      required: true
    }
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const localExcelTable = ref(props.modelValue);
    const showOptionalSettings = ref(false);
    const updateParent = () => {
      emit("update:modelValue", localExcelTable.value);
    };
    watch(
      () => props.modelValue,
      (newVal) => {
        localExcelTable.value = newVal;
      },
      { deep: true }
    );
    return (_ctx, _cache) => {
      const _component_el_input = resolveComponent("el-input");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          _cache[1] || (_cache[1] = createBaseVNode("label", { for: "sheet-name" }, "Sheet Name:", -1)),
          createVNode(_component_el_input, {
            id: "sheet-name",
            modelValue: localExcelTable.value.sheet_name,
            "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => localExcelTable.value.sheet_name = $event),
            type: "text",
            required: "",
            size: "small",
            onInput: updateParent
          }, null, 8, ["modelValue"]),
          showOptionalSettings.value ? (openBlock(), createElementBlock("hr", _hoisted_3)) : createCommentVNode("", true)
        ])
      ]);
    };
  }
});
const ExcelTableConfig = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-5d1c6e86"]]);
export {
  ExcelTableConfig as default
};
