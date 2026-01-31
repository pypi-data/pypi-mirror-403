import { d as defineComponent, r as ref, J as onMounted, c as createElementBlock, a as createBaseVNode, T as renderSlot, C as createBlock, n as normalizeClass, a0 as normalizeStyle, t as toDisplayString, e as createCommentVNode, ao as Teleport, a1 as nextTick, aw as useCssVars, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "popover-container" };
const _hoisted_2 = { key: 0 };
const _hoisted_3 = ["innerHTML"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "PopOver",
  props: {
    content: {
      type: String,
      required: true
    },
    title: {
      type: String,
      default: ""
    },
    placement: {
      type: String,
      default: "top"
    },
    minWidth: {
      type: Number,
      default: 100
    },
    zIndex: {
      type: Number,
      default: 9999
    }
  },
  setup(__props) {
    useCssVars((_ctx) => ({
      "v355ab648": props.minWidth + "px"
    }));
    const visible = ref(false);
    const referenceEl = ref(null);
    const popoverEl = ref(null);
    const props = __props;
    const popoverStyle = ref({
      top: "0px",
      left: "0px",
      zIndex: props.zIndex.toString()
    });
    const showPopover = () => {
      visible.value = true;
      nextTick(() => {
        updatePosition();
      });
    };
    const hidePopover = () => {
      visible.value = false;
    };
    const updatePosition = () => {
      if (!referenceEl.value || !popoverEl.value) return;
      const referenceRect = referenceEl.value.getBoundingClientRect();
      const popoverRect = popoverEl.value.getBoundingClientRect();
      const offset = 20;
      let top = 0;
      let left = 0;
      switch (props.placement) {
        case "top":
          top = referenceRect.top - popoverRect.height - offset;
          left = referenceRect.left + referenceRect.width / 2 - popoverRect.width / 2;
          break;
        case "bottom":
          top = referenceRect.bottom + offset;
          left = referenceRect.left + referenceRect.width / 2 - popoverRect.width / 2;
          break;
        case "left":
          top = referenceRect.top + referenceRect.height / 2 - popoverRect.height / 2;
          left = referenceRect.left - popoverRect.width - offset;
          break;
        case "right":
          top = referenceRect.top + referenceRect.height / 2 - popoverRect.height / 2;
          left = referenceRect.right + offset;
          break;
      }
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      if (left < 10) left = 10;
      if (left + popoverRect.width > viewportWidth - 10) {
        left = viewportWidth - popoverRect.width - 10;
      }
      if (top < 10) top = 10;
      if (top + popoverRect.height > viewportHeight - 10) {
        top = viewportHeight - popoverRect.height - 10;
      }
      popoverStyle.value = {
        top: `${top}px`,
        left: `${left}px`,
        zIndex: props.zIndex.toString()
      };
    };
    onMounted(() => {
      window.addEventListener("resize", () => {
        if (visible.value) {
          updatePosition();
        }
      });
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", {
          ref_key: "referenceEl",
          ref: referenceEl,
          class: "popover-reference",
          onMouseenter: showPopover,
          onMouseleave: hidePopover
        }, [
          renderSlot(_ctx.$slots, "default", {}, void 0, true)
        ], 544),
        visible.value ? (openBlock(), createBlock(Teleport, {
          key: 0,
          to: "body"
        }, [
          createBaseVNode("div", {
            ref_key: "popoverEl",
            ref: popoverEl,
            style: normalizeStyle(popoverStyle.value),
            class: normalizeClass(["popover", { "popover--left": props.placement === "left" }])
          }, [
            props.title !== "" ? (openBlock(), createElementBlock("h3", _hoisted_2, toDisplayString(props.title), 1)) : createCommentVNode("", true),
            createBaseVNode("p", {
              class: "content",
              innerHTML: props.content
            }, null, 8, _hoisted_3)
          ], 6)
        ])) : createCommentVNode("", true)
      ]);
    };
  }
});
const PopOver = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-8b5d0b86"]]);
export {
  PopOver as P
};
