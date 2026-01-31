import { d as defineComponent, c as createElementBlock, a as createBaseVNode, t as toDisplayString, K as Fragment, L as renderList, f as createTextVNode, e as createCommentVNode, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "listbox-wrapper" };
const _hoisted_2 = { class: "listbox-row" };
const _hoisted_3 = { class: "listbox-subtitle" };
const _hoisted_4 = { class: "items-container" };
const _hoisted_5 = { key: 0 };
const _hoisted_6 = ["onClick"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "SettingsSection",
  props: {
    title: { type: String, required: true },
    items: { type: Array, required: true }
  },
  emits: ["removeItem"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    const emitRemove = (item) => {
      emit("removeItem", item);
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", _hoisted_3, toDisplayString(__props.title), 1),
          createBaseVNode("div", _hoisted_4, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(__props.items, (item, index) => {
              return openBlock(), createElementBlock("div", {
                key: index,
                class: "item-box"
              }, [
                item !== "" ? (openBlock(), createElementBlock("div", _hoisted_5, [
                  createTextVNode(toDisplayString(item) + " ", 1),
                  createBaseVNode("span", {
                    class: "remove-btn",
                    onClick: ($event) => emitRemove(item)
                  }, "x", 8, _hoisted_6)
                ])) : createCommentVNode("", true)
              ]);
            }), 128))
          ])
        ])
      ]);
    };
  }
});
const SettingsSection = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-b9db7ed5"]]);
export {
  SettingsSection as default
};
