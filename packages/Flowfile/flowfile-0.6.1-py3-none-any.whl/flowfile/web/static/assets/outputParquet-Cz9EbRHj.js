import { d as defineComponent, r as ref, H as watch, c as createElementBlock, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "parquet-table-settings" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "outputParquet",
  props: {
    modelValue: {
      type: Object,
      required: true
    }
  },
  emits: ["update:modelValue"],
  setup(__props) {
    const props = __props;
    const localParquetTable = ref(props.modelValue);
    watch(
      () => props.modelValue,
      (newVal) => {
        localParquetTable.value = newVal;
      },
      { deep: true }
    );
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1);
    };
  }
});
const ParquetTableConfig = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-13145634"]]);
export {
  ParquetTableConfig as default
};
