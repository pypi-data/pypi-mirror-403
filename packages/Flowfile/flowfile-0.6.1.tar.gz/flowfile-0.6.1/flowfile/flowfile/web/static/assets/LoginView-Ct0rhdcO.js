import { d as defineComponent, u as useAuthStore, c as createElementBlock, a as createBaseVNode, b as createStaticVNode, w as withModifiers, t as toDisplayString, e as createCommentVNode, h as withDirectives, v as vModelText, i as vModelDynamic, n as normalizeClass, r as ref, _ as _imports_1, j as useRouter, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "login-container" };
const _hoisted_2 = { class: "login-card" };
const _hoisted_3 = {
  key: 0,
  class: "error-message"
};
const _hoisted_4 = { class: "form-field" };
const _hoisted_5 = { class: "input-wrapper" };
const _hoisted_6 = ["disabled"];
const _hoisted_7 = { class: "form-field" };
const _hoisted_8 = { class: "input-wrapper" };
const _hoisted_9 = ["type", "disabled"];
const _hoisted_10 = ["disabled"];
const _hoisted_11 = {
  key: 0,
  class: "loading-spinner"
};
const _hoisted_12 = { key: 1 };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "LoginView",
  setup(__props) {
    const router = useRouter();
    const authStore = useAuthStore();
    const username = ref("");
    const password = ref("");
    const showPassword = ref(false);
    const isLoading = ref(false);
    const error = ref("");
    const handleLogin = async () => {
      if (!username.value || !password.value) {
        return;
      }
      isLoading.value = true;
      error.value = "";
      try {
        const success = await authStore.login(username.value, password.value);
        if (success) {
          router.push({ name: "designer" });
        } else {
          error.value = authStore.authError || "Invalid username or password";
        }
      } catch (err) {
        error.value = "An error occurred during login. Please try again.";
        console.error("Login error:", err);
      } finally {
        isLoading.value = false;
      }
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          _cache[8] || (_cache[8] = createStaticVNode('<div class="login-header" data-v-eb9035bd><div class="logo-container" data-v-eb9035bd><img src="' + _imports_1 + '" alt="Flowfile" class="logo" data-v-eb9035bd></div><h1 class="login-title" data-v-eb9035bd>Welcome to Flowfile</h1><p class="login-subtitle" data-v-eb9035bd>Sign in to continue</p></div>', 1)),
          createBaseVNode("form", {
            class: "login-form",
            onSubmit: withModifiers(handleLogin, ["prevent"])
          }, [
            error.value ? (openBlock(), createElementBlock("div", _hoisted_3, [
              _cache[3] || (_cache[3] = createBaseVNode("i", { class: "fa-solid fa-circle-exclamation" }, null, -1)),
              createBaseVNode("span", null, toDisplayString(error.value), 1)
            ])) : createCommentVNode("", true),
            createBaseVNode("div", _hoisted_4, [
              _cache[5] || (_cache[5] = createBaseVNode("label", {
                for: "username",
                class: "form-label"
              }, "Username", -1)),
              createBaseVNode("div", _hoisted_5, [
                _cache[4] || (_cache[4] = createBaseVNode("i", { class: "fa-solid fa-user input-icon" }, null, -1)),
                withDirectives(createBaseVNode("input", {
                  id: "username",
                  "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => username.value = $event),
                  type: "text",
                  class: "form-input with-icon",
                  placeholder: "Enter your username",
                  required: "",
                  autocomplete: "username",
                  disabled: isLoading.value
                }, null, 8, _hoisted_6), [
                  [vModelText, username.value]
                ])
              ])
            ]),
            createBaseVNode("div", _hoisted_7, [
              _cache[7] || (_cache[7] = createBaseVNode("label", {
                for: "password",
                class: "form-label"
              }, "Password", -1)),
              createBaseVNode("div", _hoisted_8, [
                _cache[6] || (_cache[6] = createBaseVNode("i", { class: "fa-solid fa-lock input-icon" }, null, -1)),
                withDirectives(createBaseVNode("input", {
                  id: "password",
                  "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => password.value = $event),
                  type: showPassword.value ? "text" : "password",
                  class: "form-input with-icon",
                  placeholder: "Enter your password",
                  required: "",
                  autocomplete: "current-password",
                  disabled: isLoading.value
                }, null, 8, _hoisted_9), [
                  [vModelDynamic, password.value]
                ]),
                createBaseVNode("button", {
                  type: "button",
                  class: "toggle-password",
                  tabindex: "-1",
                  onClick: _cache[2] || (_cache[2] = ($event) => showPassword.value = !showPassword.value)
                }, [
                  createBaseVNode("i", {
                    class: normalizeClass(showPassword.value ? "fa-solid fa-eye-slash" : "fa-solid fa-eye")
                  }, null, 2)
                ])
              ])
            ]),
            createBaseVNode("button", {
              type: "submit",
              class: "btn btn-primary login-button",
              disabled: isLoading.value || !username.value || !password.value
            }, [
              isLoading.value ? (openBlock(), createElementBlock("span", _hoisted_11)) : (openBlock(), createElementBlock("span", _hoisted_12, "Sign In"))
            ], 8, _hoisted_10)
          ], 32),
          _cache[9] || (_cache[9] = createBaseVNode("div", { class: "login-footer" }, [
            createBaseVNode("p", { class: "footer-text" }, "Flowfile - Visual Data Processing")
          ], -1))
        ])
      ]);
    };
  }
});
const LoginView = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-eb9035bd"]]);
export {
  LoginView as default
};
