import { h as createSelectInputFromName } from "./node.types-Dl4gtSW9.js";
import { C as CodeLoader } from "./vue-content-loader.es-CMoRXo7N.js";
import { d as defineComponent, l as useNodeStore, J as onMounted, a1 as nextTick, x as onUnmounted, c as createElementBlock, z as createVNode, B as withCtx, A as unref, C as createBlock, r as ref, o as openBlock, G as computed, g as _export_sfc } from "./index-bcuE0Z0p.js";
import { u as useNodeSettings } from "./useNodeSettings-dMS9zmh_.js";
import { s as selectDynamic } from "./selectDynamic-Bl5FVsME.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-BBtW_Cpz.js";
import "./UnavailableFields-Yf6XSqFB.js";
import "./PopOver-BHpt5rsj.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Unique",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const showContextMenu = ref(false);
    const showContextMenuRemove = ref(false);
    const dataLoaded = ref(false);
    const contextMenuColumn = ref(null);
    const contextMenuRef = ref(null);
    const nodeUnique = ref(null);
    const nodeData = ref(null);
    const selection = ref([]);
    const uniqueInput = ref({
      columns: [],
      strategy: "any"
    });
    const getMissingColumns = (availableColumns, usedColumns) => {
      const availableSet = new Set(availableColumns);
      return Array.from(new Set(usedColumns.filter((usedColumn) => !availableSet.has(usedColumn))));
    };
    const missingColumns = computed(() => {
      var _a, _b;
      if (nodeData.value && ((_a = nodeData.value.main_input) == null ? void 0 : _a.columns)) {
        return getMissingColumns((_b = nodeData.value.main_input) == null ? void 0 : _b.columns, uniqueInput.value.columns);
      }
      return [];
    });
    const calculateMissingColumns = () => {
      var _a, _b;
      if (nodeData.value && ((_a = nodeData.value.main_input) == null ? void 0 : _a.columns)) {
        return getMissingColumns((_b = nodeData.value.main_input) == null ? void 0 : _b.columns, uniqueInput.value.columns);
      }
      return [];
    };
    const loadData = async (nodeId) => {
      var _a;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeUnique.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      dataLoaded.value = true;
      if (nodeData.value) {
        if (nodeUnique.value) {
          if (nodeUnique.value.unique_input) {
            uniqueInput.value = nodeUnique.value.unique_input;
          } else {
            nodeUnique.value.unique_input = uniqueInput.value;
          }
          loadSelection(nodeData.value, uniqueInput.value.columns);
        }
      }
    };
    const validateNode = async () => {
      var _a, _b;
      if ((_a = nodeUnique.value) == null ? void 0 : _a.unique_input) {
        await loadData(Number(nodeUnique.value.node_id));
      }
      const missingColumnsLocal = calculateMissingColumns();
      if (missingColumnsLocal.length > 0 && nodeUnique.value) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: false,
          error: `The fields ${missingColumns.value.join(", ")} are missing in the available columns.`
        });
      } else if (((_b = nodeUnique.value) == null ? void 0 : _b.unique_input.columns.length) == 0) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: false,
          error: "Please select at least one field."
        });
      } else if (nodeUnique.value) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: true,
          error: ""
        });
      }
    };
    const instantValidate = async () => {
      var _a;
      if (missingColumns.value.length > 0 && nodeUnique.value) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: false,
          error: `The fields ${missingColumns.value.join(", ")} are missing in the available columns.`
        });
      } else if (((_a = nodeUnique.value) == null ? void 0 : _a.unique_input.columns.length) == 0) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: false,
          error: "Please select at least one field."
        });
      } else if (nodeUnique.value) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: true,
          error: ""
        });
      }
    };
    const setUniqueColumns = () => {
      uniqueInput.value.columns = selection.value.filter((input) => input.keep).map((input) => input.old_name);
    };
    const { saveSettings, pushNodeData, handleGenericSettingsUpdate } = useNodeSettings({
      nodeRef: nodeUnique,
      onBeforeSave: () => {
        setUniqueColumns();
        return true;
      },
      onAfterSave: async () => {
        await instantValidate();
      },
      getValidationFunc: () => {
        var _a;
        if ((_a = nodeUnique.value) == null ? void 0 : _a.unique_input) {
          return validateNode;
        }
        return void 0;
      }
    });
    const loadSelection = (nodeData2, columnsToKeep) => {
      var _a;
      if ((_a = nodeData2.main_input) == null ? void 0 : _a.columns) {
        selection.value = nodeData2.main_input.columns.map((column) => {
          const keep = columnsToKeep.includes(column);
          return createSelectInputFromName(column, keep);
        });
      }
    };
    const calculateSelects = (updatedInputs) => {
      selection.value = updatedInputs;
      uniqueInput.value.columns = updatedInputs.filter((input) => input.keep).map((input) => input.old_name);
    };
    const loadNodeData = async (nodeId) => {
      loadData(nodeId);
      dataLoaded.value = true;
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
      return dataLoaded.value && nodeUnique.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeUnique.value,
          "onUpdate:modelValue": [
            _cache[0] || (_cache[0] = ($event) => nodeUnique.value = $event),
            unref(handleGenericSettingsUpdate)
          ],
          onRequestSave: unref(saveSettings)
        }, {
          default: withCtx(() => [
            createVNode(selectDynamic, {
              "select-inputs": selection.value,
              "show-keep-option": true,
              "show-data-type": false,
              "show-new-columns": false,
              "show-old-columns": true,
              "show-headers": true,
              "show-title": false,
              "show-data": true,
              title: "Select data",
              "original-column-header": "Column",
              onUpdateSelectInputs: calculateSelects
            }, null, 8, ["select-inputs"])
          ]),
          _: 1
        }, 8, ["modelValue", "onUpdate:modelValue", "onRequestSave"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const Unique = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-962dc284"]]);
export {
  Unique as default
};
