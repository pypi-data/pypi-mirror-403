import { d as defineComponent, l as useNodeStore, J as onMounted, a1 as nextTick, x as onUnmounted, c as createElementBlock, z as createVNode, B as withCtx, a as createBaseVNode, f as createTextVNode, h as withDirectives, v as vModelText, A as unref, e as createCommentVNode, r as ref, D as resolveComponent, o as openBlock } from "./index-bcuE0Z0p.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = { class: "listbox-wrapper" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Sample",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const showContextMenu = ref(false);
    const showContextMenuRemove = ref(false);
    const dataLoaded = ref(false);
    const contextMenuColumn = ref(null);
    const contextMenuRef = ref(null);
    const nodeSample = ref(null);
    const nodeData = ref(null);
    const sampleSize = ref(1e3);
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeSample,
      onBeforeSave: () => {
        if (nodeSample.value) {
          nodeSample.value.sample_size = sampleSize.value;
        }
        return true;
      }
    });
    const loadNodeData = async (nodeId) => {
      var _a;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeSample.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      if (nodeSample.value) {
        if (!nodeSample.value.is_setup) {
          nodeSample.value.sample_size = sampleSize.value;
        } else {
          sampleSize.value = nodeSample.value.sample_size;
        }
        dataLoaded.value = true;
      }
    };
    const handleClickOutside = (event) => {
      var _a;
      if (!((_a = contextMenuRef.value) == null ? void 0 : _a.contains(event.target))) {
        showContextMenu.value = false;
        contextMenuColumn.value = null;
        showContextMenuRemove.value = false;
      }
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
      const _component_el_col = resolveComponent("el-col");
      const _component_el_row = resolveComponent("el-row");
      return dataLoaded.value && nodeSample.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeSample.value,
          "onUpdate:modelValue": [
            _cache[1] || (_cache[1] = ($event) => nodeSample.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => [
            createBaseVNode("div", _hoisted_2, [
              _cache[3] || (_cache[3] = createBaseVNode("div", { class: "listbox-subtitle" }, "Settings", -1)),
              createVNode(_component_el_row, null, {
                default: withCtx(() => [
                  createVNode(_component_el_col, {
                    span: 10,
                    class: "grid-content"
                  }, {
                    default: withCtx(() => [..._cache[2] || (_cache[2] = [
                      createTextVNode("Offset", -1)
                    ])]),
                    _: 1
                  }),
                  createVNode(_component_el_col, {
                    span: 8,
                    class: "grid-content"
                  }, {
                    default: withCtx(() => [
                      withDirectives(createBaseVNode("input", {
                        "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => sampleSize.value = $event),
                        type: "number",
                        min: "0",
                        step: "1"
                      }, null, 512), [
                        [vModelText, sampleSize.value]
                      ])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              })
            ])
          ]),
          _: 1
        }, 8, ["modelValue", "onUpdate:modelValue", "onRequestSave"])
      ])) : createCommentVNode("", true);
    };
  }
});
export {
  _sfc_main as default
};
