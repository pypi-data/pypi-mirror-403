import { l as useNodeStore, r as ref } from "./index-bcuE0Z0p.js";
function useNodeSettings(options) {
  const { nodeRef, onBeforeSave, onAfterSave, getValidationFunc, autoSetIsSetup = true } = options;
  const nodeStore = useNodeStore();
  const isSaving = ref(false);
  const saveSettings = async () => {
    if (!nodeRef.value) {
      console.warn("useNodeSettings: Cannot save - nodeRef is null");
      return false;
    }
    if (onBeforeSave) {
      const shouldContinue = await onBeforeSave();
      if (shouldContinue === false) {
        return false;
      }
    }
    isSaving.value = true;
    try {
      if (autoSetIsSetup && nodeRef.value.is_setup !== void 0) {
        nodeRef.value.is_setup = true;
      }
      await nodeStore.updateSettings(nodeRef);
      if (onAfterSave) {
        await onAfterSave();
      }
      if (getValidationFunc) {
        const validateFunc = getValidationFunc();
        if (validateFunc && nodeRef.value) {
          nodeStore.setNodeValidateFunc(nodeRef.value.node_id, validateFunc);
        }
      }
      return true;
    } catch (error) {
      console.error("useNodeSettings: Error saving settings:", error);
      return false;
    } finally {
      isSaving.value = false;
    }
  };
  const pushNodeData = async () => {
    await saveSettings();
  };
  const handleGenericSettingsUpdate = (updatedNode) => {
    if (!nodeRef.value) return;
    nodeRef.value.cache_results = updatedNode.cache_results;
    nodeRef.value.description = updatedNode.description;
    nodeRef.value.output_field_config = updatedNode.output_field_config;
    if (updatedNode.pos_x !== void 0) {
      nodeRef.value.pos_x = updatedNode.pos_x;
    }
    if (updatedNode.pos_y !== void 0) {
      nodeRef.value.pos_y = updatedNode.pos_y;
    }
    for (const key in updatedNode) {
      if (key in nodeRef.value && key !== "cache_results" && key !== "description" && key !== "output_field_config" && key !== "pos_x" && key !== "pos_y") {
        nodeRef.value[key] = updatedNode[key];
      }
    }
  };
  return {
    isSaving,
    saveSettings,
    pushNodeData,
    handleGenericSettingsUpdate
  };
}
export {
  useNodeSettings as u
};
