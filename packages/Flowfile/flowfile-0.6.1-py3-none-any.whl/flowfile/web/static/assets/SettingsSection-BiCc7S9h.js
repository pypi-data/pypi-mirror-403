import { d as defineComponent, c as createElementBlock, a as createBaseVNode, a0 as normalizeStyle, t as toDisplayString, K as Fragment, L as renderList, f as createTextVNode, e as createCommentVNode, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "listbox-wrapper" };
const _hoisted_2 = { class: "listbox-row" };
const _hoisted_3 = { class: "items-container" };
const _hoisted_4 = { key: 0 };
const _hoisted_5 = ["onClick"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "SettingsSection",
  props: {
    title: { type: String, required: true },
    titleFontSize: { type: String, default: "15px" },
    items: { type: Array, required: true }
  },
  emits: ["removeItem"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const emitRemove = (item) => {
      emit("removeItem", item);
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", {
            class: "listbox-title",
            style: normalizeStyle({ fontSize: props.titleFontSize })
          }, toDisplayString(__props.title), 5),
          createBaseVNode("div", _hoisted_3, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(__props.items, (item, index) => {
              return openBlock(), createElementBlock("div", {
                key: index,
                class: "item-box"
              }, [
                item !== "" ? (openBlock(), createElementBlock("div", _hoisted_4, [
                  createTextVNode(toDisplayString(item) + " ", 1),
                  createBaseVNode("span", {
                    class: "remove-btn",
                    onClick: ($event) => emitRemove(item)
                  }, "x", 8, _hoisted_5)
                ])) : createCommentVNode("", true)
              ]);
            }), 128))
          ])
        ])
      ]);
    };
  }
});
const SettingsSection = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-1a44e29e"]]);
export {
  SettingsSection as default
};
