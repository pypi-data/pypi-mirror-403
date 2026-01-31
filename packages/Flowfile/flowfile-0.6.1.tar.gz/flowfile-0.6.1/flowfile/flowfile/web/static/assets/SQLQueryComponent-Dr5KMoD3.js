import { d as defineComponent, c as createElementBlock, a as createBaseVNode, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "query-section" };
const _hoisted_2 = { class: "form-group" };
const _hoisted_3 = ["value"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "SQLQueryComponent",
  props: {
    modelValue: {}
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    const onInput = (event) => {
      const target = event.target;
      emit("update:modelValue", target.value);
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        _cache[0] || (_cache[0] = createBaseVNode("h4", { class: "section-subtitle" }, "SQL Query", -1)),
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("textarea", {
            id: "query",
            value: __props.modelValue,
            class: "form-control textarea",
            placeholder: "Enter SQL query",
            rows: "4",
            onInput
          }, null, 40, _hoisted_3)
        ])
      ]);
    };
  }
});
const SqlQueryComponent = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-10f7cdfb"]]);
export {
  SqlQueryComponent as default
};
