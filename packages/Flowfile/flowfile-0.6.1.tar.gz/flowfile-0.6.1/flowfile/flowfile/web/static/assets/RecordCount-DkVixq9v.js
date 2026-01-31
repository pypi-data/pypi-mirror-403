import { d as defineComponent, l as useNodeStore, J as onMounted, a1 as nextTick, c as createElementBlock, z as createVNode, B as withCtx, a as createBaseVNode, A as unref, e as createCommentVNode, r as ref, o as openBlock } from "./index-bcuE0Z0p.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "RecordCount",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const nodeData = ref(null);
    const nodeRecordCount = ref(null);
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeRecordCount
    });
    const loadNodeData = async (nodeId) => {
      var _a;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeRecordCount.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      if (nodeRecordCount.value) {
        dataLoaded.value = true;
      }
    };
    __expose({
      loadNodeData,
      pushNodeData,
      saveSettings
    });
    onMounted(async () => {
      await nextTick();
    });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodeRecordCount.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeRecordCount.value,
          "onUpdate:modelValue": [
            _cache[0] || (_cache[0] = ($event) => nodeRecordCount.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => [..._cache[1] || (_cache[1] = [
            createBaseVNode("p", null, " This node helps you quickly retrieve the total number of records from the selected table. It's a simple yet powerful tool to keep track of the data volume as you work through your tasks. ", -1),
            createBaseVNode("p", null, "This node does not need a setup", -1)
          ])]),
          _: 1
        }, 8, ["modelValue", "onUpdate:modelValue", "onRequestSave"])
      ])) : createCommentVNode("", true);
    };
  }
});
export {
  _sfc_main as default
};
