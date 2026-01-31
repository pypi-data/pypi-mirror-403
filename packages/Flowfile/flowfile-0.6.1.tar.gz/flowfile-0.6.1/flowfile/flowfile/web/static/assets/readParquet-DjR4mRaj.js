import { d as defineComponent, c as createElementBlock, a as createBaseVNode, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "parquet-table-settings" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "readParquet",
  props: {
    modelValue: {}
  },
  setup(__props) {
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [..._cache[0] || (_cache[0] = [
        createBaseVNode("div", { class: "message" }, [
          createBaseVNode("h2", null, "You are ready to flow!"),
          createBaseVNode("p", null, "Your Parquet table setup is complete. Enjoy the smooth data processing experience.")
        ], -1)
      ])]);
    };
  }
});
const ParquetTableConfig = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-25b5bc22"]]);
export {
  ParquetTableConfig as default
};
