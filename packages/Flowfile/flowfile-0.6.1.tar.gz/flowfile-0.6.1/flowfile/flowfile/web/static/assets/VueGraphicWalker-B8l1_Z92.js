const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/index-DPkoZWq8.js","assets/index-bcuE0Z0p.js","assets/index-UFXyfirV.css","assets/index-DnW_KC_I.js","assets/client-C8Ygr6Gb.js","assets/index-BCJxPfM5.js","assets/graphic-walker.es-VrK6vdGE.js"])))=>i.map(i=>d[i]);
import { d as defineComponent, J as onMounted, al as __vitePreload, x as onUnmounted, c as createElementBlock, t as toDisplayString, e as createCommentVNode, h as withDirectives, at as vShow, a as createBaseVNode, r as ref, aB as toRaw, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
const _hoisted_1 = { class: "gw-wrapper" };
const _hoisted_2 = {
  key: 0,
  class: "loading"
};
const _hoisted_3 = {
  key: 1,
  class: "error"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "VueGraphicWalker",
  props: {
    data: {},
    fields: {},
    specList: {},
    appearance: {},
    themeKey: {}
  },
  setup(__props, { expose: __expose }) {
    const props = __props;
    const container = ref(null);
    const isLoading = ref(true);
    const loadError = ref(null);
    let reactRootInstance = null;
    let React = null;
    let ReactDOMClient = null;
    let GraphicWalker = null;
    const internalStoreRef = ref({ current: null });
    const dummyComputation = async () => {
      console.warn(
        "Dummy computation function called. This should not happen when providing local data."
      );
      return [];
    };
    const getReactProps = () => {
      const chartSpecArray = props.specList ? toRaw(props.specList) : [];
      const reactProps = {
        data: props.data ? toRaw(props.data) : void 0,
        fields: props.fields ? toRaw(props.fields) : void 0,
        appearance: props.appearance || "light",
        themeKey: props.themeKey,
        storeRef: internalStoreRef.value,
        ...chartSpecArray.length > 0 && { chart: chartSpecArray },
        computation: dummyComputation
      };
      Object.keys(reactProps).forEach((key) => {
        if (reactProps[key] === void 0) {
          delete reactProps[key];
        }
      });
      return reactProps;
    };
    onMounted(async () => {
      if (!container.value) {
        console.error("[VueGW] Container element not found for mounting.");
        loadError.value = "Container not found";
        isLoading.value = false;
        return;
      }
      try {
        const [reactModule, reactDomModule, gwModule] = await Promise.all([
          __vitePreload(() => import("./index-DPkoZWq8.js").then((n) => n.t), true ? __vite__mapDeps([0,1,2,3]) : void 0),
          __vitePreload(() => import("./client-C8Ygr6Gb.js").then((n) => n.c), true ? __vite__mapDeps([4,1,2,5,3]) : void 0),
          __vitePreload(() => import("./graphic-walker.es-VrK6vdGE.js"), true ? __vite__mapDeps([6,0,1,2,3,5]) : void 0)
        ]);
        React = reactModule.default;
        ReactDOMClient = reactDomModule;
        GraphicWalker = gwModule.GraphicWalker;
        reactRootInstance = ReactDOMClient.createRoot(container.value);
        const componentProps = getReactProps();
        reactRootInstance.render(React.createElement(GraphicWalker, componentProps));
        isLoading.value = false;
      } catch (e) {
        console.error("[VueGW] Error mounting GraphicWalker:", e);
        loadError.value = e instanceof Error ? e.message : "Failed to load";
        isLoading.value = false;
      }
    });
    onUnmounted(() => {
      if (reactRootInstance) {
        reactRootInstance.unmount();
        reactRootInstance = null;
      }
    });
    const exportCode = async () => {
      var _a;
      const storeInstance = (_a = internalStoreRef.value) == null ? void 0 : _a.current;
      if (!storeInstance) {
        console.error(
          "[VueGW] Cannot export code: Store instance is not available.",
          internalStoreRef.value
        );
        return null;
      }
      if (typeof storeInstance.exportCode !== "function") {
        console.error(
          "[VueGW] Cannot export code: 'exportCode' method not found on store instance.",
          storeInstance
        );
        return null;
      }
      try {
        const result = await storeInstance.exportCode();
        return result ?? [];
      } catch (error) {
        console.error("[VueGW] Error during exportCode execution:", error);
        return null;
      }
    };
    __expose({
      exportCode
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        isLoading.value ? (openBlock(), createElementBlock("div", _hoisted_2, "Loading visualization...")) : loadError.value ? (openBlock(), createElementBlock("div", _hoisted_3, toDisplayString(loadError.value), 1)) : createCommentVNode("", true),
        withDirectives(createBaseVNode("div", {
          ref_key: "container",
          ref: container
        }, null, 512), [
          [vShow, !isLoading.value && !loadError.value]
        ])
      ]);
    };
  }
});
const VueGraphicWalker = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-503e510b"]]);
export {
  VueGraphicWalker as default
};
