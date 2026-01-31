import { C as CodeLoader } from "./vue-content-loader.es-CMoRXo7N.js";
import { d as defineComponent, l as useNodeStore, c as createElementBlock, z as createVNode, B as withCtx, a as createBaseVNode, A as unref, C as createBlock, r as ref, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import { s as selectDynamic } from "./selectDynamic-Bl5FVsME.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
import "./UnavailableFields-Yf6XSqFB.js";
import "./PopOver-BHpt5rsj.js";
const _hoisted_1 = { key: 0 };
const _hoisted_2 = { class: "listbox-wrapper" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "CrossJoin",
  setup(__props, { expose: __expose }) {
    const result = ref(null);
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const nodeCrossJoin = ref(null);
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeCrossJoin
    });
    const updateSelectInputsHandler = (updatedInputs, isLeft) => {
      if (isLeft && nodeCrossJoin.value) {
        nodeCrossJoin.value.cross_join_input.left_select.renames = updatedInputs;
      } else if (nodeCrossJoin.value) {
        nodeCrossJoin.value.cross_join_input.right_select.renames = updatedInputs;
      }
    };
    const loadNodeData = async (nodeId) => {
      var _a;
      result.value = await nodeStore.getNodeData(nodeId, false);
      nodeCrossJoin.value = (_a = result.value) == null ? void 0 : _a.setting_input;
      console.log(result.value);
      if (result.value) {
        console.log("Data loaded");
        dataLoaded.value = true;
      }
    };
    __expose({
      loadNodeData,
      pushNodeData,
      saveSettings
    });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodeCrossJoin.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeCrossJoin.value,
          "onUpdate:modelValue": [
            _cache[2] || (_cache[2] = ($event) => nodeCrossJoin.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => {
            var _a, _b;
            return [
              createBaseVNode("div", _hoisted_2, [
                createVNode(selectDynamic, {
                  "select-inputs": (_a = nodeCrossJoin.value) == null ? void 0 : _a.cross_join_input.left_select.renames,
                  "show-keep-option": true,
                  "show-title": true,
                  "show-headers": true,
                  "show-data": true,
                  title: "Left data",
                  onUpdateSelectInputs: _cache[0] || (_cache[0] = (updatedInputs) => updateSelectInputsHandler(updatedInputs, true))
                }, null, 8, ["select-inputs"]),
                createVNode(selectDynamic, {
                  "select-inputs": (_b = nodeCrossJoin.value) == null ? void 0 : _b.cross_join_input.right_select.renames,
                  "show-keep-option": true,
                  "show-headers": true,
                  "show-title": true,
                  "show-data": true,
                  title: "Right data",
                  onUpdateSelectInputs: _cache[1] || (_cache[1] = (updatedInputs) => updateSelectInputsHandler(updatedInputs, false))
                }, null, 8, ["select-inputs"])
              ])
            ];
          }),
          _: 1
        }, 8, ["modelValue", "onUpdate:modelValue", "onRequestSave"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const CrossJoin = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-789bbdab"]]);
export {
  CrossJoin as default
};
