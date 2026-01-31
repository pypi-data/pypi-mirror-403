import { d as defineComponent, c as createElementBlock, a as createBaseVNode, G as computed, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "doc-wrapper" };
const _hoisted_2 = ["src"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "DocumentationView",
  setup(__props) {
    const docsUrl = computed(
      () => "https://edwardvaneechoud.github.io/Flowfile/"
    );
    const openFlowfile = () => {
      window.open(docsUrl.value);
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("iframe", {
          src: docsUrl.value,
          class: "iframe-docs"
        }, null, 8, _hoisted_2),
        createBaseVNode("button", {
          class: "flowfile-button",
          onClick: openFlowfile
        }, [..._cache[0] || (_cache[0] = [
          createBaseVNode("i", { class: "fas fa-up-right-from-square" }, null, -1)
        ])])
      ]);
    };
  }
});
const DocumentationView = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-93c4b98d"]]);
export {
  DocumentationView as default
};
