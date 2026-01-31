import { d as defineComponent, l as useNodeStore, J as onMounted, a1 as nextTick, x as onUnmounted, c as createElementBlock, z as createVNode, B as withCtx, f as createTextVNode, A as unref, e as createCommentVNode, r as ref, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Union",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const showContextMenu = ref(false);
    const dataLoaded = ref(false);
    const nodeData = ref(null);
    const unionInput = ref({ mode: "relaxed" });
    const nodeUnion = ref(null);
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeUnion
    });
    const loadNodeData = async (nodeId) => {
      var _a;
      console.log("loadNodeData from union ");
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeUnion.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      if (nodeData.value) {
        if (nodeUnion.value) {
          if (nodeUnion.value.union_input) {
            unionInput.value = nodeUnion.value.union_input;
          } else {
            nodeUnion.value.union_input = unionInput.value;
          }
        }
      }
      dataLoaded.value = true;
      console.log("loadNodeData from groupby");
    };
    const handleClickOutside = (event) => {
      const targetEvent = event.target;
      if (targetEvent.id === "pivot-context-menu") return;
      showContextMenu.value = false;
    };
    __expose({
      loadNodeData,
      pushNodeData,
      saveSettings
    });
    onMounted(async () => {
      await nextTick();
      window.addEventListener("click", handleClickOutside);
    });
    onUnmounted(() => {
      window.removeEventListener("click", handleClickOutside);
    });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodeUnion.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeUnion.value,
          "onUpdate:modelValue": [
            _cache[0] || (_cache[0] = ($event) => nodeUnion.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => [..._cache[1] || (_cache[1] = [
            createTextVNode(" 'Union multiple tables into one table, this node does not have settings' ", -1)
          ])]),
          _: 1
        }, 8, ["modelValue", "onUpdate:modelValue", "onRequestSave"])
      ])) : createCommentVNode("", true);
    };
  }
});
const Union = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-2380ae5e"]]);
export {
  Union as default
};
