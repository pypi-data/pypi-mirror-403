import { d as defineComponent, J as onMounted, c as createElementBlock, a as createBaseVNode, f as createTextVNode, t as toDisplayString, e as createCommentVNode, z as createVNode, B as withCtx, K as Fragment, L as renderList, C as createBlock, r as ref, G as computed, D as resolveComponent, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
import { S as SecretsApi } from "./secrets.api-C9o2KE5V.js";
const _hoisted_1 = { class: "component-container" };
const _hoisted_2 = { class: "listbox-subtitle" };
const _hoisted_3 = {
  key: 0,
  class: "required-indicator"
};
const _hoisted_4 = {
  key: 0,
  class: "field-description"
};
const _hoisted_5 = { class: "secret-option" };
const _hoisted_6 = {
  key: 1,
  class: "no-secrets-hint"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "SecretSelector",
  props: {
    schema: {
      type: Object,
      required: true
    },
    modelValue: {
      type: String,
      default: null
    }
  },
  emits: ["update:modelValue"],
  setup(__props) {
    const props = __props;
    const secrets = ref([]);
    const loading = ref(true);
    const filteredSecrets = computed(() => {
      if (!props.schema.name_prefix) {
        return secrets.value;
      }
      return secrets.value.filter(
        (secret) => secret.name.toLowerCase().startsWith(props.schema.name_prefix.toLowerCase())
      );
    });
    const loadSecrets = async () => {
      loading.value = true;
      try {
        secrets.value = await SecretsApi.getAll();
      } catch (error) {
        console.error("Failed to load secrets:", error);
        secrets.value = [];
      } finally {
        loading.value = false;
      }
    };
    const openSecretsManager = () => {
      window.open("/#/secrets", "_blank");
    };
    onMounted(() => {
      loadSecrets();
    });
    return (_ctx, _cache) => {
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("label", _hoisted_2, [
          createTextVNode(toDisplayString(__props.schema.label) + " ", 1),
          __props.schema.required ? (openBlock(), createElementBlock("span", _hoisted_3, "*")) : createCommentVNode("", true)
        ]),
        __props.schema.description ? (openBlock(), createElementBlock("p", _hoisted_4, toDisplayString(__props.schema.description), 1)) : createCommentVNode("", true),
        createVNode(_component_el_select, {
          "model-value": __props.modelValue,
          filterable: "",
          clearable: "",
          placeholder: "Select a secret",
          style: { "width": "100%" },
          size: "large",
          loading: loading.value,
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => _ctx.$emit("update:modelValue", $event))
        }, {
          default: withCtx(() => [
            (openBlock(true), createElementBlock(Fragment, null, renderList(filteredSecrets.value, (secret) => {
              return openBlock(), createBlock(_component_el_option, {
                key: secret.name,
                label: secret.name,
                value: secret.name
              }, {
                default: withCtx(() => [
                  createBaseVNode("div", _hoisted_5, [
                    _cache[1] || (_cache[1] = createBaseVNode("i", { class: "fa-solid fa-key secret-icon" }, null, -1)),
                    createBaseVNode("span", null, toDisplayString(secret.name), 1)
                  ])
                ]),
                _: 2
              }, 1032, ["label", "value"]);
            }), 128))
          ]),
          _: 1
        }, 8, ["model-value", "loading"]),
        !loading.value && filteredSecrets.value.length === 0 ? (openBlock(), createElementBlock("p", _hoisted_6, [
          _cache[2] || (_cache[2] = createTextVNode(" No secrets available. ", -1)),
          createBaseVNode("span", {
            class: "hint-link",
            onClick: openSecretsManager
          }, "Add secrets")
        ])) : createCommentVNode("", true)
      ]);
    };
  }
});
const SecretSelector = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-c7dfd4de"]]);
export {
  SecretSelector as default
};
