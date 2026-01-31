import { d as defineComponent, J as onMounted, x as onUnmounted, c as createElementBlock, a0 as normalizeStyle, a as createBaseVNode, K as Fragment, L as renderList, n as normalizeClass, t as toDisplayString, r as ref, o as openBlock } from "./index-bcuE0Z0p.js";
const _hoisted_1 = ["onClick"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "ContextMenu",
  props: {
    position: {},
    options: {}
  },
  emits: ["select", "close"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    const menuRef = ref(null);
    const selectOption = (option) => {
      if (option.disabled) return;
      emit("select", option.action);
      emit("close");
    };
    const handleClickOutside = (event) => {
      if (menuRef.value && !menuRef.value.contains(event.target)) {
        emit("close");
      }
    };
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        emit("close");
      }
    };
    onMounted(() => {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    });
    onUnmounted(() => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        ref_key: "menuRef",
        ref: menuRef,
        class: "context-menu",
        style: normalizeStyle({ top: __props.position.y + "px", left: __props.position.x + "px" })
      }, [
        createBaseVNode("ul", null, [
          (openBlock(true), createElementBlock(Fragment, null, renderList(__props.options, (option) => {
            return openBlock(), createElementBlock("li", {
              key: option.action,
              class: normalizeClass({ disabled: option.disabled, danger: option.danger }),
              onClick: ($event) => selectOption(option)
            }, toDisplayString(option.label), 11, _hoisted_1);
          }), 128))
        ])
      ], 4);
    };
  }
});
export {
  _sfc_main as _
};
