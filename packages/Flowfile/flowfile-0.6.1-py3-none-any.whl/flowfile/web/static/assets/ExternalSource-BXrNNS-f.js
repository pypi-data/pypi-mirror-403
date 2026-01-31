import { C as CodeLoader } from "./vue-content-loader.es-CMoRXo7N.js";
import { d as defineComponent, l as useNodeStore, ah as watchEffect, c as createElementBlock, z as createVNode, B as withCtx, a as createBaseVNode, K as Fragment, L as renderList, e as createCommentVNode, C as createBlock, A as unref, r as ref, D as resolveComponent, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
function get_template_source_type(type, options) {
  switch (type) {
    case "SAMPLE_USERS":
      return {
        SAMPLE_USERS: true,
        size: (options == null ? void 0 : options.size) || 100,
        // Default size is 100 if not provided
        orientation: (options == null ? void 0 : options.orientation) || "row",
        // Default orientation is 'ROWS'
        fields: []
      };
    default:
      throw new Error("Unsupported configuration type");
  }
}
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = {
  key: 0,
  class: "file-upload-container"
};
const _hoisted_3 = {
  key: 0,
  class: "file-upload-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "ExternalSource",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const nodeExternalSource = ref(null);
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeExternalSource,
      onBeforeSave: async () => {
        if (nodeExternalSource.value && isDirty.value) {
          nodeExternalSource.value.is_setup = true;
          nodeExternalSource.value.source_settings.fields = [];
          isDirty.value = false;
        }
        return true;
      },
      onAfterSave: async () => {
        if (nodeExternalSource.value) {
          await nodeStore.getNodeData(Number(nodeExternalSource.value.node_id), false);
        }
      }
    });
    const sampleUsers = ref(null);
    const dataLoaded = ref(false);
    const typeSelected = ref(false);
    const writingOptions = ["sample_users"];
    const selectedExternalSource = ref(null);
    const isDirty = ref(false);
    watchEffect(() => {
    });
    const loadNodeData = async (nodeId) => {
      const nodeResult = await nodeStore.getNodeData(nodeId, false);
      nodeExternalSource.value = nodeResult == null ? void 0 : nodeResult.setting_input;
      if (nodeExternalSource.value) {
        if (nodeExternalSource.value.is_setup) {
          if (nodeExternalSource.value.identifier == "sample_users") {
            sampleUsers.value = nodeExternalSource.value.source_settings;
            selectedExternalSource.value = "sample_users";
          }
        }
        typeSelected.value = true;
        dataLoaded.value = true;
        isDirty.value = false;
      }
    };
    const loadTemplateValue = () => {
      console.log(selectedExternalSource.value);
      if (selectedExternalSource.value === "sample_users") {
        sampleUsers.value = get_template_source_type("SAMPLE_USERS");
        if (nodeExternalSource.value) {
          nodeExternalSource.value.source_settings = sampleUsers.value;
        }
        isDirty.value = true;
      }
      typeSelected.value = true;
      if (nodeExternalSource.value && selectedExternalSource.value) {
        nodeExternalSource.value.identifier = selectedExternalSource.value;
      }
    };
    __expose({
      loadNodeData,
      pushNodeData,
      saveSettings
    });
    return (_ctx, _cache) => {
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      return dataLoaded.value && nodeExternalSource.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeExternalSource.value,
          "onUpdate:modelValue": [
            _cache[1] || (_cache[1] = ($event) => nodeExternalSource.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => [
            _cache[2] || (_cache[2] = createBaseVNode("div", { class: "listbox-subtitle" }, "Select the type of external source", -1)),
            createVNode(_component_el_select, {
              modelValue: selectedExternalSource.value,
              "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => selectedExternalSource.value = $event),
              class: "m-2",
              placeholder: "Select type of external source",
              size: "small",
              onChange: loadTemplateValue
            }, {
              default: withCtx(() => [
                (openBlock(), createElementBlock(Fragment, null, renderList(writingOptions, (item) => {
                  return createVNode(_component_el_option, {
                    key: item,
                    label: item,
                    value: item
                  }, null, 8, ["label", "value"]);
                }), 64))
              ]),
              _: 1
            }, 8, ["modelValue"]),
            typeSelected.value ? (openBlock(), createElementBlock("div", _hoisted_2, [
              selectedExternalSource.value === "sample_users" && sampleUsers.value ? (openBlock(), createElementBlock("div", _hoisted_3)) : createCommentVNode("", true)
            ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }))
          ]),
          _: 1
        }, 8, ["modelValue", "onUpdate:modelValue", "onRequestSave"])
      ])) : createCommentVNode("", true);
    };
  }
});
const ExternalSource = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-f2824e05"]]);
export {
  ExternalSource as default
};
