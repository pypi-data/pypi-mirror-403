import { d as defineComponent, C as createBlock, B as withCtx, a as createBaseVNode, c as createElementBlock, e as createCommentVNode, z as createVNode, A as unref, aC as ElIcon, aK as ElPopover, G as computed, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "validation-wrapper" };
const _hoisted_2 = {
  key: 0,
  class: "error-message"
};
const _hoisted_3 = {
  key: 1,
  class: "error-message"
};
const _hoisted_4 = {
  key: 2,
  class: "error-message"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "PivotValidation",
  props: {
    pivotInput: {}
  },
  setup(__props) {
    const props = __props;
    const showValidationMessages = computed(() => {
      return !props.pivotInput.pivot_column || !props.pivotInput.value_col || props.pivotInput.aggregations.length === 0;
    });
    return (_ctx, _cache) => {
      return showValidationMessages.value ? (openBlock(), createBlock(unref(ElPopover), {
        key: 0,
        placement: "top",
        width: "200",
        trigger: "hover",
        content: "Some required fields are missing"
      }, {
        reference: withCtx(() => [
          createVNode(unref(ElIcon), {
            color: "#FF6B6B",
            class: "warning-icon"
          }, {
            default: withCtx(() => [..._cache[0] || (_cache[0] = [
              createBaseVNode("i", { class: "el-icon-warning" }, null, -1)
            ])]),
            _: 1
          })
        ]),
        default: withCtx(() => [
          createBaseVNode("div", _hoisted_1, [
            !__props.pivotInput.pivot_column ? (openBlock(), createElementBlock("p", _hoisted_2, "Pivot Column cannot be empty.")) : createCommentVNode("", true),
            !__props.pivotInput.value_col ? (openBlock(), createElementBlock("p", _hoisted_3, "Value Column cannot be empty.")) : createCommentVNode("", true),
            __props.pivotInput.aggregations.length === 0 ? (openBlock(), createElementBlock("p", _hoisted_4, " At least one aggregation must be selected. ")) : createCommentVNode("", true)
          ])
        ]),
        _: 1
      })) : createCommentVNode("", true);
    };
  }
});
const PivotValidation = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-30064f3f"]]);
export {
  PivotValidation as default
};
