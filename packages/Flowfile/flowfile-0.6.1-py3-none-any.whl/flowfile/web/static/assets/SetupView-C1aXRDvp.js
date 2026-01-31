import { d as defineComponent, c as createElementBlock, a as createBaseVNode, b as createStaticVNode, t as toDisplayString, e as createCommentVNode, n as normalizeClass, f as createTextVNode, r as ref, s as setupService, o as openBlock, _ as _imports_1, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "setup-container" };
const _hoisted_2 = { class: "setup-card" };
const _hoisted_3 = { class: "setup-content" };
const _hoisted_4 = {
  key: 0,
  class: "error-message"
};
const _hoisted_5 = {
  key: 1,
  class: "generate-section"
};
const _hoisted_6 = ["disabled"];
const _hoisted_7 = {
  key: 0,
  class: "loading-spinner"
};
const _hoisted_8 = {
  key: 1,
  class: "fa-solid fa-key"
};
const _hoisted_9 = {
  key: 2,
  class: "key-result"
};
const _hoisted_10 = { class: "key-display" };
const _hoisted_11 = { class: "key-value-wrapper" };
const _hoisted_12 = { class: "key-value" };
const _hoisted_13 = { class: "instructions-box" };
const _hoisted_14 = { class: "instruction-content" };
const _hoisted_15 = { class: "code-block" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "SetupView",
  setup(__props) {
    const isGenerating = ref(false);
    const error = ref("");
    const generatedKey = ref(null);
    const copied = ref(false);
    const copiedEnv = ref(false);
    const handleGenerateKey = async () => {
      isGenerating.value = true;
      error.value = "";
      try {
        generatedKey.value = await setupService.generateKey();
      } catch (err) {
        error.value = "Failed to generate key. Please check if the backend is running.";
        console.error("Generate key error:", err);
      } finally {
        isGenerating.value = false;
      }
    };
    const copyToClipboard = async (text, flagRef) => {
      try {
        await navigator.clipboard.writeText(text);
        flagRef.value = true;
        setTimeout(() => {
          flagRef.value = false;
        }, 2e3);
      } catch (err) {
        console.error("Failed to copy:", err);
      }
    };
    const copyKey = () => {
      if (generatedKey.value) {
        copyToClipboard(generatedKey.value.key, copied);
      }
    };
    const copyEnvVar = () => {
      if (generatedKey.value) {
        copyToClipboard(`FLOWFILE_MASTER_KEY="${generatedKey.value.key}"`, copiedEnv);
      }
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          _cache[7] || (_cache[7] = createStaticVNode('<div class="setup-header" data-v-0c48ff2a><div class="logo-container" data-v-0c48ff2a><img src="' + _imports_1 + '" alt="Flowfile" class="logo" data-v-0c48ff2a></div><h1 class="setup-title" data-v-0c48ff2a>Initial Setup Required</h1><p class="setup-subtitle" data-v-0c48ff2a>Configure your master encryption key to get started</p></div>', 1)),
          createBaseVNode("div", _hoisted_3, [
            _cache[6] || (_cache[6] = createBaseVNode("div", { class: "info-box" }, [
              createBaseVNode("i", { class: "fa-solid fa-shield-halved info-icon" }),
              createBaseVNode("div", { class: "info-text" }, [
                createBaseVNode("h3", null, "What is the Master Key?"),
                createBaseVNode("p", null, " The master key encrypts all secrets stored in Flowfile (API keys, passwords, tokens). It must be configured before the application can be used. ")
              ])
            ], -1)),
            error.value ? (openBlock(), createElementBlock("div", _hoisted_4, [
              _cache[0] || (_cache[0] = createBaseVNode("i", { class: "fa-solid fa-circle-exclamation" }, null, -1)),
              createBaseVNode("span", null, toDisplayString(error.value), 1)
            ])) : createCommentVNode("", true),
            !generatedKey.value ? (openBlock(), createElementBlock("div", _hoisted_5, [
              createBaseVNode("button", {
                class: "btn btn-primary generate-button",
                disabled: isGenerating.value,
                onClick: handleGenerateKey
              }, [
                isGenerating.value ? (openBlock(), createElementBlock("span", _hoisted_7)) : (openBlock(), createElementBlock("i", _hoisted_8)),
                createBaseVNode("span", null, toDisplayString(isGenerating.value ? "Generating..." : "Generate Master Key"), 1)
              ], 8, _hoisted_6)
            ])) : (openBlock(), createElementBlock("div", _hoisted_9, [
              createBaseVNode("div", _hoisted_10, [
                _cache[1] || (_cache[1] = createBaseVNode("label", { class: "key-label" }, "Your Generated Master Key:", -1)),
                createBaseVNode("div", _hoisted_11, [
                  createBaseVNode("code", _hoisted_12, toDisplayString(generatedKey.value.key), 1),
                  createBaseVNode("button", {
                    class: "copy-button",
                    title: "Copy to clipboard",
                    onClick: copyKey
                  }, [
                    createBaseVNode("i", {
                      class: normalizeClass(copied.value ? "fa-solid fa-check" : "fa-solid fa-copy")
                    }, null, 2)
                  ])
                ])
              ]),
              createBaseVNode("div", _hoisted_13, [
                _cache[4] || (_cache[4] = createBaseVNode("h4", null, "Configuration Instructions:", -1)),
                createBaseVNode("div", _hoisted_14, [
                  _cache[2] || (_cache[2] = createBaseVNode("p", null, [
                    createTextVNode("Add this line to a "),
                    createBaseVNode("code", null, ".env"),
                    createTextVNode(" file in your project root:")
                  ], -1)),
                  createBaseVNode("div", _hoisted_15, [
                    createBaseVNode("code", null, 'FLOWFILE_MASTER_KEY="' + toDisplayString(generatedKey.value.key) + '"', 1),
                    createBaseVNode("button", {
                      class: "copy-button small",
                      onClick: copyEnvVar
                    }, [
                      createBaseVNode("i", {
                        class: normalizeClass(copiedEnv.value ? "fa-solid fa-check" : "fa-solid fa-copy")
                      }, null, 2)
                    ])
                  ]),
                  _cache[3] || (_cache[3] = createBaseVNode("p", { class: "hint" }, [
                    createTextVNode(" Then restart: "),
                    createBaseVNode("code", null, "docker-compose down && docker-compose up")
                  ], -1))
                ])
              ]),
              _cache[5] || (_cache[5] = createBaseVNode("div", { class: "warning-box" }, [
                createBaseVNode("i", { class: "fa-solid fa-triangle-exclamation" }),
                createBaseVNode("div", null, [
                  createBaseVNode("strong", null, "Important:"),
                  createTextVNode(" Back up this key securely. If lost, all stored secrets become unrecoverable. ")
                ])
              ], -1))
            ]))
          ]),
          _cache[8] || (_cache[8] = createBaseVNode("div", { class: "setup-footer" }, [
            createBaseVNode("p", { class: "footer-text" }, "Flowfile - Visual Data Processing")
          ], -1))
        ])
      ]);
    };
  }
});
const SetupView = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-0c48ff2a"]]);
export {
  SetupView as default
};
