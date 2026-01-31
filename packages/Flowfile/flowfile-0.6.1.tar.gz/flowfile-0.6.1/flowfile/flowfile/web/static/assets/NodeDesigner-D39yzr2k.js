import { d as defineComponent, c as createElementBlock, a as createBaseVNode, K as Fragment, L as renderList, A as unref, n as normalizeClass, t as toDisplayString, o as openBlock, g as _export_sfc, w as withModifiers, e as createCommentVNode, r as ref, f as createTextVNode, b as createStaticVNode, z as createVNode, J as onMounted, k as axios, G as computed, a5 as reactive, H as watch, h as withDirectives, v as vModelText, a6 as isRef, C as createBlock } from "./index-bcuE0Z0p.js";
import { T, k as keymap, a as acceptCompletion, i as indentMore, b as indentLess, c as EditorState, d as autocompletion, P as Prec, E as EditorView } from "./vue-codemirror.esm-CwaYwln0.js";
import { g as getImageUrl, _ as __vite_glob_0_33, a as __vite_glob_0_32, b as __vite_glob_0_31, c as __vite_glob_0_30, d as __vite_glob_0_29, e as __vite_glob_0_28, h as __vite_glob_0_27, i as __vite_glob_0_26, j as __vite_glob_0_25, k as __vite_glob_0_24, l as __vite_glob_0_23, m as __vite_glob_0_22, n as __vite_glob_0_21, q as __vite_glob_0_20, r as __vite_glob_0_19, s as __vite_glob_0_18, t as __vite_glob_0_17, u as __vite_glob_0_16, v as __vite_glob_0_15, w as __vite_glob_0_14, x as __vite_glob_0_13, y as __vite_glob_0_12, z as __vite_glob_0_11, A as __vite_glob_0_10, B as __vite_glob_0_9, C as __vite_glob_0_8, D as __vite_glob_0_7, E as __vite_glob_0_6, F as __vite_glob_0_5, G as __vite_glob_0_4, H as __vite_glob_0_3, I as __vite_glob_0_2, J as __vite_glob_0_1, K as __vite_glob_0_0, L as getDefaultIconUrl, M as getCustomIconUrl, o as oneDark, p as python } from "./index-CHPMUR0d.js";
const STORAGE_KEY = "nodeDesigner_state";
const availableComponents = [
  { type: "TextInput", label: "Text Input", icon: "fa-solid fa-font" },
  { type: "NumericInput", label: "Numeric Input", icon: "fa-solid fa-hashtag" },
  { type: "ToggleSwitch", label: "Toggle Switch", icon: "fa-solid fa-toggle-on" },
  { type: "SingleSelect", label: "Single Select", icon: "fa-solid fa-list" },
  { type: "MultiSelect", label: "Multi Select", icon: "fa-solid fa-list-check" },
  { type: "ColumnSelector", label: "Column Selector", icon: "fa-solid fa-table-columns" },
  { type: "ColumnActionInput", label: "Column Action", icon: "fa-solid fa-table-list" },
  { type: "SliderInput", label: "Slider", icon: "fa-solid fa-sliders" },
  { type: "SecretSelector", label: "Secret Selector", icon: "fa-solid fa-key" }
];
const defaultProcessCode = `def process(self, *inputs: pl.LazyFrame) -> pl.LazyFrame:
    # Get the first input LazyFrame
    lf = inputs[0]

    # Your transformation logic here
    # Example: lf = lf.filter(pl.col("column") > 0)

    return lf`;
const defaultNodeMetadata = {
  node_name: "",
  node_category: "Custom",
  title: "",
  intro: "",
  number_of_inputs: 1,
  number_of_outputs: 1,
  node_icon: "user-defined-icon.png"
};
function getComponentIcon(type) {
  const comp = availableComponents.find((c) => c.type === type);
  return (comp == null ? void 0 : comp.icon) || "fa-solid fa-puzzle-piece";
}
const _hoisted_1$a = { class: "panel component-palette" };
const _hoisted_2$a = { class: "panel-content" };
const _hoisted_3$9 = ["onDragstart"];
const _sfc_main$a = /* @__PURE__ */ defineComponent({
  __name: "ComponentPalette",
  emits: ["dragstart"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    function handleDragStart(event, component) {
      var _a;
      (_a = event.dataTransfer) == null ? void 0 : _a.setData("component_type", component.type);
      emit("dragstart", event, component);
    }
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$a, [
        _cache[0] || (_cache[0] = createBaseVNode("div", { class: "panel-header" }, [
          createBaseVNode("h3", null, "Components")
        ], -1)),
        createBaseVNode("div", _hoisted_2$a, [
          (openBlock(true), createElementBlock(Fragment, null, renderList(unref(availableComponents), (comp) => {
            return openBlock(), createElementBlock("div", {
              key: comp.type,
              class: "component-item",
              draggable: "true",
              onDragstart: ($event) => handleDragStart($event, comp)
            }, [
              createBaseVNode("i", {
                class: normalizeClass(comp.icon)
              }, null, 2),
              createBaseVNode("span", null, toDisplayString(comp.label), 1)
            ], 40, _hoisted_3$9);
          }), 128))
        ])
      ]);
    };
  }
});
const ComponentPalette = /* @__PURE__ */ _export_sfc(_sfc_main$a, [["__scopeId", "data-v-7eeb4ea6"]]);
const _hoisted_1$9 = { class: "section-header" };
const _hoisted_2$9 = { class: "section-fields" };
const _hoisted_3$8 = { class: "section-field" };
const _hoisted_4$7 = ["value"];
const _hoisted_5$5 = { class: "section-field" };
const _hoisted_6$5 = ["value"];
const _hoisted_7$5 = ["onClick"];
const _hoisted_8$5 = { class: "component-preview" };
const _hoisted_9$5 = { class: "component-label" };
const _hoisted_10$5 = { class: "component-type" };
const _hoisted_11$5 = ["onClick"];
const _hoisted_12$4 = {
  key: 0,
  class: "drop-zone"
};
const _sfc_main$9 = /* @__PURE__ */ defineComponent({
  __name: "SectionCard",
  props: {
    section: {},
    isSelected: { type: Boolean },
    selectedComponentIndex: {}
  },
  emits: ["select", "remove", "selectComponent", "removeComponent", "drop", "updateName", "updateTitle"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    function handleNameChange(event) {
      const target = event.target;
      emit("updateName", target.value);
    }
    function handleTitleChange(event) {
      const target = event.target;
      emit("updateTitle", target.value);
    }
    function handleDrop(event) {
      emit("drop", event);
    }
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        class: normalizeClass(["section-card", { selected: __props.isSelected }]),
        onClick: _cache[4] || (_cache[4] = ($event) => emit("select"))
      }, [
        createBaseVNode("div", _hoisted_1$9, [
          createBaseVNode("div", _hoisted_2$9, [
            createBaseVNode("div", _hoisted_3$8, [
              _cache[5] || (_cache[5] = createBaseVNode("label", null, "Variable Name", -1)),
              createBaseVNode("input", {
                value: __props.section.name,
                type: "text",
                class: "section-name-input",
                placeholder: "section_name",
                onClick: _cache[0] || (_cache[0] = withModifiers(() => {
                }, ["stop"])),
                onInput: handleNameChange
              }, null, 40, _hoisted_4$7)
            ]),
            createBaseVNode("div", _hoisted_5$5, [
              _cache[6] || (_cache[6] = createBaseVNode("label", null, "Display Title", -1)),
              createBaseVNode("input", {
                value: __props.section.title,
                type: "text",
                class: "section-title-input",
                placeholder: "Section Title",
                onClick: _cache[1] || (_cache[1] = withModifiers(() => {
                }, ["stop"])),
                onInput: handleTitleChange
              }, null, 40, _hoisted_6$5)
            ])
          ]),
          createBaseVNode("button", {
            class: "btn-icon",
            onClick: _cache[2] || (_cache[2] = withModifiers(($event) => emit("remove"), ["stop"]))
          }, [..._cache[7] || (_cache[7] = [
            createBaseVNode("i", { class: "fa-solid fa-trash" }, null, -1)
          ])])
        ]),
        createBaseVNode("div", {
          class: "section-components",
          onDragover: _cache[3] || (_cache[3] = withModifiers(() => {
          }, ["prevent"])),
          onDrop: handleDrop
        }, [
          (openBlock(true), createElementBlock(Fragment, null, renderList(__props.section.components, (component, compIndex) => {
            return openBlock(), createElementBlock("div", {
              key: compIndex,
              class: normalizeClass(["component-card", { selected: __props.isSelected && __props.selectedComponentIndex === compIndex }]),
              onClick: withModifiers(($event) => emit("selectComponent", compIndex), ["stop"])
            }, [
              createBaseVNode("div", _hoisted_8$5, [
                createBaseVNode("i", {
                  class: normalizeClass(unref(getComponentIcon)(component.component_type))
                }, null, 2),
                createBaseVNode("span", _hoisted_9$5, toDisplayString(component.label || component.component_type), 1),
                createBaseVNode("span", _hoisted_10$5, "(" + toDisplayString(component.component_type) + ")", 1)
              ]),
              createBaseVNode("button", {
                class: "btn-icon btn-remove",
                onClick: withModifiers(($event) => emit("removeComponent", compIndex), ["stop"])
              }, [..._cache[8] || (_cache[8] = [
                createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
              ])], 8, _hoisted_11$5)
            ], 10, _hoisted_7$5);
          }), 128)),
          __props.section.components.length === 0 ? (openBlock(), createElementBlock("div", _hoisted_12$4, [..._cache[9] || (_cache[9] = [
            createBaseVNode("i", { class: "fa-solid fa-plus" }, null, -1),
            createBaseVNode("span", null, "Drop components here", -1)
          ])])) : createCommentVNode("", true)
        ], 32)
      ], 2);
    };
  }
});
const SectionCard = /* @__PURE__ */ _export_sfc(_sfc_main$9, [["__scopeId", "data-v-17318956"]]);
function toSnakeCase(str) {
  return str.replace(/\s+/g, "_").replace(/([a-z])([A-Z])/g, "$1_$2").toLowerCase().replace(/[^a-z0-9_]/g, "");
}
function toPascalCase(str) {
  return str.split(/[\s_-]+/).map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join("");
}
function useCodeGeneration() {
  const showPreviewModal = ref(false);
  const generatedCode = ref("");
  function generateCode(nodeMetadata, sections, processCode) {
    const nodeName = toPascalCase(nodeMetadata.node_name || "MyCustomNode");
    const nodeSettingsName = `${nodeName}Settings`;
    const imports = /* @__PURE__ */ new Set();
    imports.add("CustomNodeBase");
    imports.add("Section");
    imports.add("NodeSettings");
    sections.forEach((section) => {
      section.components.forEach((comp) => {
        imports.add(comp.component_type);
        if (comp.options_source === "incoming_columns") {
          imports.add("IncomingColumns");
        }
      });
    });
    let sectionsCode = "";
    sections.forEach((section) => {
      const sectionName = section.name || toSnakeCase(section.title || "section");
      const sectionTitle = section.title || section.name || "Section";
      sectionsCode += `
# ${sectionTitle}
`;
      sectionsCode += `${sectionName} = Section(
`;
      sectionsCode += `    title="${sectionTitle}",
`;
      section.components.forEach((comp) => {
        const fieldName = toSnakeCase(comp.field_name);
        sectionsCode += `    ${fieldName}=${comp.component_type}(
`;
        sectionsCode += `        label="${comp.label || fieldName}",
`;
        if (comp.component_type === "TextInput") {
          if (comp.default) sectionsCode += `        default="${comp.default}",
`;
          if (comp.placeholder) sectionsCode += `        placeholder="${comp.placeholder}",
`;
        } else if (comp.component_type === "NumericInput") {
          if (comp.default !== void 0) sectionsCode += `        default=${comp.default},
`;
          if (comp.min_value !== void 0)
            sectionsCode += `        min_value=${comp.min_value},
`;
          if (comp.max_value !== void 0)
            sectionsCode += `        max_value=${comp.max_value},
`;
        } else if (comp.component_type === "ToggleSwitch") {
          sectionsCode += `        default=${comp.default ? "True" : "False"},
`;
          if (comp.description) sectionsCode += `        description="${comp.description}",
`;
        } else if (comp.component_type === "SingleSelect" || comp.component_type === "MultiSelect") {
          if (comp.options_source === "incoming_columns") {
            sectionsCode += `        options=IncomingColumns,
`;
          } else if (comp.options_string) {
            const options = comp.options_string.split(",").map((o) => `"${o.trim()}"`).join(", ");
            sectionsCode += `        options=[${options}],
`;
          }
        } else if (comp.component_type === "ColumnSelector") {
          if (comp.required) sectionsCode += `        required=True,
`;
          if (comp.multiple) sectionsCode += `        multiple=True,
`;
          if (comp.data_types && comp.data_types !== "ALL") {
            sectionsCode += `        data_types="${comp.data_types}",
`;
          }
        } else if (comp.component_type === "SliderInput") {
          sectionsCode += `        min_value=${comp.min_value ?? 0},
`;
          sectionsCode += `        max_value=${comp.max_value ?? 100},
`;
          if (comp.step) sectionsCode += `        step=${comp.step},
`;
        } else if (comp.component_type === "SecretSelector") {
          if (comp.required) sectionsCode += `        required=True,
`;
          if (comp.description) sectionsCode += `        description="${comp.description}",
`;
          if (comp.name_prefix) sectionsCode += `        name_prefix="${comp.name_prefix}",
`;
        } else if (comp.component_type === "ColumnActionInput") {
          if (comp.actions_string) {
            const actions = comp.actions_string.split(",").map((a) => `"${a.trim()}"`).join(", ");
            sectionsCode += `        actions=[${actions}],
`;
          }
          if (comp.output_name_template) {
            sectionsCode += `        output_name_template="${comp.output_name_template}",
`;
          }
          if (comp.show_group_by) sectionsCode += `        show_group_by=True,
`;
          if (comp.show_order_by) sectionsCode += `        show_order_by=True,
`;
          if (comp.data_types && comp.data_types !== "ALL") {
            sectionsCode += `        data_types="${comp.data_types}",
`;
          }
        }
        sectionsCode += `    ),
`;
      });
      sectionsCode += `)
`;
    });
    let settingsCode = `
class ${nodeSettingsName}(NodeSettings):
`;
    sections.forEach((section) => {
      const sectionName = section.name || toSnakeCase(section.title || "section");
      settingsCode += `    ${sectionName}: Section = ${sectionName}
`;
    });
    if (sections.length === 0) {
      settingsCode += `    pass
`;
    }
    let processBody = processCode;
    const defMatch = processBody.match(/def\s+process\s*\([^)]*\)\s*->\s*[^:]+:\n?/);
    if (defMatch) {
      processBody = processBody.substring(defMatch[0].length);
    }
    const lines = processBody.split("\n");
    const nonEmptyLines = lines.filter((line) => line.trim().length > 0);
    let minIndent = 0;
    if (nonEmptyLines.length > 0) {
      minIndent = Math.min(
        ...nonEmptyLines.map((line) => {
          const match = line.match(/^(\s*)/);
          return match ? match[1].length : 0;
        })
      );
    }
    const reindentedLines = lines.map((line) => {
      if (line.trim().length === 0) {
        return "";
      }
      const dedented = line.length >= minIndent ? line.substring(minIndent) : line.trimStart();
      return "        " + dedented;
    });
    processBody = reindentedLines.join("\n");
    const nodeCode = `

class ${nodeName}(CustomNodeBase):
    node_name: str = "${nodeMetadata.node_name}"
    node_category: str = "${nodeMetadata.node_category}"
    node_icon: str = "${nodeMetadata.node_icon || "user-defined-icon.png"}"
    title: str = "${nodeMetadata.title || nodeMetadata.node_name}"
    intro: str = "${nodeMetadata.intro || "A custom node for data processing"}"
    number_of_inputs: int = ${nodeMetadata.number_of_inputs}
    number_of_outputs: int = ${nodeMetadata.number_of_outputs}
    settings_schema: ${nodeSettingsName} = ${nodeSettingsName}()

    def process(self, *inputs: pl.LazyFrame) -> pl.LazyFrame:
${processBody}
`;
    const secretStrImport = processCode.includes("SecretStr") ? "from pydantic import SecretStr\n" : "";
    const fullCode = `# Auto-generated custom node
# Generated by Node Designer

import polars as pl
${secretStrImport}from flowfile_core.flowfile.node_designer import (
    ${Array.from(imports).join(", ")}
)
${sectionsCode}${settingsCode}${nodeCode}`;
    return fullCode;
  }
  function previewCode(nodeMetadata, sections, processCode) {
    generatedCode.value = generateCode(nodeMetadata, sections, processCode);
    showPreviewModal.value = true;
  }
  function closePreview() {
    showPreviewModal.value = false;
  }
  function copyCode() {
    navigator.clipboard.writeText(generatedCode.value);
    alert("Code copied to clipboard!");
  }
  return {
    showPreviewModal,
    generatedCode,
    generateCode,
    previewCode,
    closePreview,
    copyCode,
    toSnakeCase,
    toPascalCase
  };
}
const _hoisted_1$8 = { class: "panel property-editor" };
const _hoisted_2$8 = { class: "panel-content" };
const _hoisted_3$7 = {
  key: 0,
  class: "property-form"
};
const _hoisted_4$6 = { class: "component-type-badge" };
const _hoisted_5$4 = { class: "property-group" };
const _hoisted_6$4 = { class: "property-row" };
const _hoisted_7$4 = ["value"];
const _hoisted_8$4 = { class: "property-row" };
const _hoisted_9$4 = ["value"];
const _hoisted_10$4 = {
  key: 0,
  class: "property-group"
};
const _hoisted_11$4 = { class: "property-row" };
const _hoisted_12$3 = ["value"];
const _hoisted_13$3 = { class: "property-row" };
const _hoisted_14$3 = ["value"];
const _hoisted_15$3 = {
  key: 1,
  class: "property-group"
};
const _hoisted_16$3 = { class: "property-row" };
const _hoisted_17$2 = ["value"];
const _hoisted_18$2 = { class: "property-row" };
const _hoisted_19$1 = ["value"];
const _hoisted_20 = { class: "property-row" };
const _hoisted_21 = ["value"];
const _hoisted_22 = {
  key: 2,
  class: "property-group"
};
const _hoisted_23 = { class: "property-row checkbox-row" };
const _hoisted_24 = ["checked"];
const _hoisted_25 = { class: "property-row" };
const _hoisted_26 = ["value"];
const _hoisted_27 = {
  key: 3,
  class: "property-group"
};
const _hoisted_28 = { class: "property-row" };
const _hoisted_29 = ["value"];
const _hoisted_30 = {
  key: 0,
  class: "property-row"
};
const _hoisted_31 = ["value"];
const _hoisted_32 = {
  key: 4,
  class: "property-group"
};
const _hoisted_33 = { class: "property-row" };
const _hoisted_34 = ["value"];
const _hoisted_35 = {
  key: 0,
  class: "property-row"
};
const _hoisted_36 = ["value"];
const _hoisted_37 = {
  key: 5,
  class: "property-group"
};
const _hoisted_38 = { class: "property-row checkbox-row" };
const _hoisted_39 = ["checked"];
const _hoisted_40 = { class: "property-row checkbox-row" };
const _hoisted_41 = ["checked"];
const _hoisted_42 = { class: "property-row" };
const _hoisted_43 = ["value"];
const _hoisted_44 = {
  key: 6,
  class: "property-group"
};
const _hoisted_45 = { class: "property-row" };
const _hoisted_46 = ["value"];
const _hoisted_47 = { class: "property-row" };
const _hoisted_48 = ["value"];
const _hoisted_49 = { class: "property-row" };
const _hoisted_50 = ["value"];
const _hoisted_51 = {
  key: 7,
  class: "property-group"
};
const _hoisted_52 = { class: "property-row" };
const _hoisted_53 = ["value"];
const _hoisted_54 = { class: "property-row" };
const _hoisted_55 = ["value"];
const _hoisted_56 = { class: "property-row" };
const _hoisted_57 = ["value"];
const _hoisted_58 = { class: "property-row checkbox-row" };
const _hoisted_59 = ["checked"];
const _hoisted_60 = { class: "property-row checkbox-row" };
const _hoisted_61 = ["checked"];
const _hoisted_62 = {
  key: 8,
  class: "property-group"
};
const _hoisted_63 = { class: "property-row checkbox-row" };
const _hoisted_64 = ["checked"];
const _hoisted_65 = { class: "property-row" };
const _hoisted_66 = ["value"];
const _hoisted_67 = { class: "property-row" };
const _hoisted_68 = ["value"];
const _hoisted_69 = {
  key: 1,
  class: "no-selection"
};
const _sfc_main$8 = /* @__PURE__ */ defineComponent({
  __name: "PropertyEditor",
  props: {
    component: {},
    sectionName: {}
  },
  emits: ["update", "insert-variable"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    function updateField(field, value) {
      emit("update", field, value);
    }
    function getTypeForComponent(componentType, multiple) {
      switch (componentType) {
        case "TextInput":
          return "str";
        case "NumericInput":
        case "SliderInput":
          return "float";
        case "ToggleSwitch":
          return "bool";
        case "SingleSelect":
          return "str";
        case "MultiSelect":
          return "list[str]";
        case "ColumnSelector":
          return multiple ? "list[str]" : "str";
        case "ColumnActionInput":
          return "dict";
        case "SecretSelector":
          return "SecretStr";
        default:
          return "Any";
      }
    }
    function insertVariable() {
      if (!props.component || !props.sectionName) return;
      const fieldName = toSnakeCase(props.component.field_name);
      const sectionName = toSnakeCase(props.sectionName);
      const pyType = getTypeForComponent(props.component.component_type, props.component.multiple);
      let code;
      if (props.component.component_type === "SecretSelector") {
        code = `    ${fieldName}: ${pyType} = self.settings_schema.${sectionName}.${fieldName}.secret_value`;
      } else {
        code = `    ${fieldName}: ${pyType} = self.settings_schema.${sectionName}.${fieldName}.value`;
      }
      emit("insert-variable", code);
    }
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$8, [
        _cache[74] || (_cache[74] = createBaseVNode("div", { class: "panel-header" }, [
          createBaseVNode("h3", null, "Properties")
        ], -1)),
        createBaseVNode("div", _hoisted_2$8, [
          __props.component ? (openBlock(), createElementBlock("div", _hoisted_3$7, [
            createBaseVNode("div", _hoisted_4$6, [
              createBaseVNode("i", {
                class: normalizeClass(unref(getComponentIcon)(__props.component.component_type))
              }, null, 2),
              createBaseVNode("span", null, toDisplayString(__props.component.component_type), 1)
            ]),
            createBaseVNode("div", _hoisted_5$4, [
              _cache[29] || (_cache[29] = createBaseVNode("div", { class: "property-group-title" }, "Basic", -1)),
              createBaseVNode("div", _hoisted_6$4, [
                _cache[27] || (_cache[27] = createBaseVNode("label", { class: "property-label" }, [
                  createTextVNode("Field Name "),
                  createBaseVNode("span", { class: "required" }, "*")
                ], -1)),
                createBaseVNode("input", {
                  value: __props.component.field_name,
                  type: "text",
                  class: "property-input",
                  placeholder: "field_name",
                  onInput: _cache[0] || (_cache[0] = ($event) => updateField("field_name", $event.target.value))
                }, null, 40, _hoisted_7$4)
              ]),
              createBaseVNode("div", _hoisted_8$4, [
                _cache[28] || (_cache[28] = createBaseVNode("label", { class: "property-label" }, "Label", -1)),
                createBaseVNode("input", {
                  value: __props.component.label,
                  type: "text",
                  class: "property-input",
                  placeholder: "Display Label",
                  onInput: _cache[1] || (_cache[1] = ($event) => updateField("label", $event.target.value))
                }, null, 40, _hoisted_9$4)
              ])
            ]),
            __props.component.component_type === "TextInput" ? (openBlock(), createElementBlock("div", _hoisted_10$4, [
              _cache[32] || (_cache[32] = createBaseVNode("div", { class: "property-group-title" }, "Text Options", -1)),
              createBaseVNode("div", _hoisted_11$4, [
                _cache[30] || (_cache[30] = createBaseVNode("label", { class: "property-label" }, "Default Value", -1)),
                createBaseVNode("input", {
                  value: __props.component.default,
                  type: "text",
                  class: "property-input",
                  placeholder: "Default value",
                  onInput: _cache[2] || (_cache[2] = ($event) => updateField("default", $event.target.value))
                }, null, 40, _hoisted_12$3)
              ]),
              createBaseVNode("div", _hoisted_13$3, [
                _cache[31] || (_cache[31] = createBaseVNode("label", { class: "property-label" }, "Placeholder", -1)),
                createBaseVNode("input", {
                  value: __props.component.placeholder,
                  type: "text",
                  class: "property-input",
                  placeholder: "Placeholder text",
                  onInput: _cache[3] || (_cache[3] = ($event) => updateField("placeholder", $event.target.value))
                }, null, 40, _hoisted_14$3)
              ])
            ])) : createCommentVNode("", true),
            __props.component.component_type === "NumericInput" ? (openBlock(), createElementBlock("div", _hoisted_15$3, [
              _cache[36] || (_cache[36] = createBaseVNode("div", { class: "property-group-title" }, "Number Options", -1)),
              createBaseVNode("div", _hoisted_16$3, [
                _cache[33] || (_cache[33] = createBaseVNode("label", { class: "property-label" }, "Default Value", -1)),
                createBaseVNode("input", {
                  value: __props.component.default,
                  type: "number",
                  class: "property-input",
                  onInput: _cache[4] || (_cache[4] = ($event) => updateField("default", Number($event.target.value)))
                }, null, 40, _hoisted_17$2)
              ]),
              createBaseVNode("div", _hoisted_18$2, [
                _cache[34] || (_cache[34] = createBaseVNode("label", { class: "property-label" }, "Min Value", -1)),
                createBaseVNode("input", {
                  value: __props.component.min_value,
                  type: "number",
                  class: "property-input",
                  onInput: _cache[5] || (_cache[5] = ($event) => updateField("min_value", Number($event.target.value)))
                }, null, 40, _hoisted_19$1)
              ]),
              createBaseVNode("div", _hoisted_20, [
                _cache[35] || (_cache[35] = createBaseVNode("label", { class: "property-label" }, "Max Value", -1)),
                createBaseVNode("input", {
                  value: __props.component.max_value,
                  type: "number",
                  class: "property-input",
                  onInput: _cache[6] || (_cache[6] = ($event) => updateField("max_value", Number($event.target.value)))
                }, null, 40, _hoisted_21)
              ])
            ])) : createCommentVNode("", true),
            __props.component.component_type === "ToggleSwitch" ? (openBlock(), createElementBlock("div", _hoisted_22, [
              _cache[39] || (_cache[39] = createBaseVNode("div", { class: "property-group-title" }, "Toggle Options", -1)),
              createBaseVNode("div", _hoisted_23, [
                _cache[37] || (_cache[37] = createBaseVNode("label", { class: "property-label" }, "Default Value", -1)),
                createBaseVNode("input", {
                  checked: __props.component.default,
                  type: "checkbox",
                  class: "property-checkbox",
                  onChange: _cache[7] || (_cache[7] = ($event) => updateField("default", $event.target.checked))
                }, null, 40, _hoisted_24)
              ]),
              createBaseVNode("div", _hoisted_25, [
                _cache[38] || (_cache[38] = createBaseVNode("label", { class: "property-label" }, "Description", -1)),
                createBaseVNode("input", {
                  value: __props.component.description,
                  type: "text",
                  class: "property-input",
                  placeholder: "Toggle description",
                  onInput: _cache[8] || (_cache[8] = ($event) => updateField("description", $event.target.value))
                }, null, 40, _hoisted_26)
              ])
            ])) : createCommentVNode("", true),
            __props.component.component_type === "SingleSelect" ? (openBlock(), createElementBlock("div", _hoisted_27, [
              _cache[43] || (_cache[43] = createBaseVNode("div", { class: "property-group-title" }, "Select Options", -1)),
              createBaseVNode("div", _hoisted_28, [
                _cache[41] || (_cache[41] = createBaseVNode("label", { class: "property-label" }, "Options Source", -1)),
                createBaseVNode("select", {
                  value: __props.component.options_source,
                  class: "property-input",
                  onChange: _cache[9] || (_cache[9] = ($event) => updateField("options_source", $event.target.value))
                }, [..._cache[40] || (_cache[40] = [
                  createBaseVNode("option", { value: "static" }, "Static Options", -1),
                  createBaseVNode("option", { value: "incoming_columns" }, "Incoming Columns", -1)
                ])], 40, _hoisted_29)
              ]),
              __props.component.options_source === "static" ? (openBlock(), createElementBlock("div", _hoisted_30, [
                _cache[42] || (_cache[42] = createBaseVNode("label", { class: "property-label" }, "Options (comma-separated)", -1)),
                createBaseVNode("input", {
                  value: __props.component.options_string,
                  type: "text",
                  class: "property-input",
                  placeholder: "option1, option2, option3",
                  onInput: _cache[10] || (_cache[10] = ($event) => updateField("options_string", $event.target.value))
                }, null, 40, _hoisted_31)
              ])) : createCommentVNode("", true)
            ])) : createCommentVNode("", true),
            __props.component.component_type === "MultiSelect" ? (openBlock(), createElementBlock("div", _hoisted_32, [
              _cache[47] || (_cache[47] = createBaseVNode("div", { class: "property-group-title" }, "Select Options", -1)),
              createBaseVNode("div", _hoisted_33, [
                _cache[45] || (_cache[45] = createBaseVNode("label", { class: "property-label" }, "Options Source", -1)),
                createBaseVNode("select", {
                  value: __props.component.options_source,
                  class: "property-input",
                  onChange: _cache[11] || (_cache[11] = ($event) => updateField("options_source", $event.target.value))
                }, [..._cache[44] || (_cache[44] = [
                  createBaseVNode("option", { value: "static" }, "Static Options", -1),
                  createBaseVNode("option", { value: "incoming_columns" }, "Incoming Columns", -1)
                ])], 40, _hoisted_34)
              ]),
              __props.component.options_source === "static" ? (openBlock(), createElementBlock("div", _hoisted_35, [
                _cache[46] || (_cache[46] = createBaseVNode("label", { class: "property-label" }, "Options (comma-separated)", -1)),
                createBaseVNode("input", {
                  value: __props.component.options_string,
                  type: "text",
                  class: "property-input",
                  placeholder: "option1, option2, option3",
                  onInput: _cache[12] || (_cache[12] = ($event) => updateField("options_string", $event.target.value))
                }, null, 40, _hoisted_36)
              ])) : createCommentVNode("", true)
            ])) : createCommentVNode("", true),
            __props.component.component_type === "ColumnSelector" ? (openBlock(), createElementBlock("div", _hoisted_37, [
              _cache[52] || (_cache[52] = createBaseVNode("div", { class: "property-group-title" }, "Column Options", -1)),
              createBaseVNode("div", _hoisted_38, [
                _cache[48] || (_cache[48] = createBaseVNode("label", { class: "property-label" }, "Required", -1)),
                createBaseVNode("input", {
                  checked: __props.component.required,
                  type: "checkbox",
                  class: "property-checkbox",
                  onChange: _cache[13] || (_cache[13] = ($event) => updateField("required", $event.target.checked))
                }, null, 40, _hoisted_39)
              ]),
              createBaseVNode("div", _hoisted_40, [
                _cache[49] || (_cache[49] = createBaseVNode("label", { class: "property-label" }, "Multiple Selection", -1)),
                createBaseVNode("input", {
                  checked: __props.component.multiple,
                  type: "checkbox",
                  class: "property-checkbox",
                  onChange: _cache[14] || (_cache[14] = ($event) => updateField("multiple", $event.target.checked))
                }, null, 40, _hoisted_41)
              ]),
              createBaseVNode("div", _hoisted_42, [
                _cache[51] || (_cache[51] = createBaseVNode("label", { class: "property-label" }, "Data Types Filter", -1)),
                createBaseVNode("select", {
                  value: __props.component.data_types,
                  class: "property-input",
                  onChange: _cache[15] || (_cache[15] = ($event) => updateField("data_types", $event.target.value))
                }, [..._cache[50] || (_cache[50] = [
                  createBaseVNode("option", { value: "ALL" }, "All Types", -1),
                  createBaseVNode("option", { value: "numeric" }, "Numeric", -1),
                  createBaseVNode("option", { value: "string" }, "String", -1),
                  createBaseVNode("option", { value: "temporal" }, "Temporal", -1)
                ])], 40, _hoisted_43)
              ])
            ])) : createCommentVNode("", true),
            __props.component.component_type === "SliderInput" ? (openBlock(), createElementBlock("div", _hoisted_44, [
              _cache[56] || (_cache[56] = createBaseVNode("div", { class: "property-group-title" }, "Slider Options", -1)),
              createBaseVNode("div", _hoisted_45, [
                _cache[53] || (_cache[53] = createBaseVNode("label", { class: "property-label" }, [
                  createTextVNode("Min Value "),
                  createBaseVNode("span", { class: "required" }, "*")
                ], -1)),
                createBaseVNode("input", {
                  value: __props.component.min_value,
                  type: "number",
                  class: "property-input",
                  onInput: _cache[16] || (_cache[16] = ($event) => updateField("min_value", Number($event.target.value)))
                }, null, 40, _hoisted_46)
              ]),
              createBaseVNode("div", _hoisted_47, [
                _cache[54] || (_cache[54] = createBaseVNode("label", { class: "property-label" }, [
                  createTextVNode("Max Value "),
                  createBaseVNode("span", { class: "required" }, "*")
                ], -1)),
                createBaseVNode("input", {
                  value: __props.component.max_value,
                  type: "number",
                  class: "property-input",
                  onInput: _cache[17] || (_cache[17] = ($event) => updateField("max_value", Number($event.target.value)))
                }, null, 40, _hoisted_48)
              ]),
              createBaseVNode("div", _hoisted_49, [
                _cache[55] || (_cache[55] = createBaseVNode("label", { class: "property-label" }, "Step", -1)),
                createBaseVNode("input", {
                  value: __props.component.step,
                  type: "number",
                  class: "property-input",
                  onInput: _cache[18] || (_cache[18] = ($event) => updateField("step", Number($event.target.value)))
                }, null, 40, _hoisted_50)
              ])
            ])) : createCommentVNode("", true),
            __props.component.component_type === "ColumnActionInput" ? (openBlock(), createElementBlock("div", _hoisted_51, [
              _cache[65] || (_cache[65] = createBaseVNode("div", { class: "property-group-title" }, "Column Action Options", -1)),
              createBaseVNode("div", _hoisted_52, [
                _cache[57] || (_cache[57] = createBaseVNode("label", { class: "property-label" }, [
                  createTextVNode("Actions (comma-separated) "),
                  createBaseVNode("span", { class: "required" }, "*")
                ], -1)),
                createBaseVNode("input", {
                  value: __props.component.actions_string,
                  type: "text",
                  class: "property-input",
                  placeholder: "sum, mean, min, max",
                  onInput: _cache[19] || (_cache[19] = ($event) => updateField("actions_string", $event.target.value))
                }, null, 40, _hoisted_53),
                _cache[58] || (_cache[58] = createBaseVNode("span", { class: "field-hint" }, "Actions available in dropdown (e.g., sum, mean, min, max)", -1))
              ]),
              createBaseVNode("div", _hoisted_54, [
                _cache[59] || (_cache[59] = createBaseVNode("label", { class: "property-label" }, "Output Name Template", -1)),
                createBaseVNode("input", {
                  value: __props.component.output_name_template,
                  type: "text",
                  class: "property-input",
                  placeholder: "{column}_{action}",
                  onInput: _cache[20] || (_cache[20] = ($event) => updateField("output_name_template", $event.target.value))
                }, null, 40, _hoisted_55),
                _cache[60] || (_cache[60] = createBaseVNode("span", { class: "field-hint" }, "Use {column} and {action} placeholders", -1))
              ]),
              createBaseVNode("div", _hoisted_56, [
                _cache[62] || (_cache[62] = createBaseVNode("label", { class: "property-label" }, "Data Types Filter", -1)),
                createBaseVNode("select", {
                  value: __props.component.data_types,
                  class: "property-input",
                  onChange: _cache[21] || (_cache[21] = ($event) => updateField("data_types", $event.target.value))
                }, [..._cache[61] || (_cache[61] = [
                  createBaseVNode("option", { value: "ALL" }, "All Types", -1),
                  createBaseVNode("option", { value: "Numeric" }, "Numeric", -1),
                  createBaseVNode("option", { value: "String" }, "String", -1),
                  createBaseVNode("option", { value: "Date" }, "Date/Time", -1)
                ])], 40, _hoisted_57)
              ]),
              createBaseVNode("div", _hoisted_58, [
                _cache[63] || (_cache[63] = createBaseVNode("label", { class: "property-label" }, "Show Group By", -1)),
                createBaseVNode("input", {
                  checked: __props.component.show_group_by,
                  type: "checkbox",
                  class: "property-checkbox",
                  onChange: _cache[22] || (_cache[22] = ($event) => updateField("show_group_by", $event.target.checked))
                }, null, 40, _hoisted_59)
              ]),
              createBaseVNode("div", _hoisted_60, [
                _cache[64] || (_cache[64] = createBaseVNode("label", { class: "property-label" }, "Show Order By", -1)),
                createBaseVNode("input", {
                  checked: __props.component.show_order_by,
                  type: "checkbox",
                  class: "property-checkbox",
                  onChange: _cache[23] || (_cache[23] = ($event) => updateField("show_order_by", $event.target.checked))
                }, null, 40, _hoisted_61)
              ])
            ])) : createCommentVNode("", true),
            __props.component.component_type === "SecretSelector" ? (openBlock(), createElementBlock("div", _hoisted_62, [
              _cache[70] || (_cache[70] = createBaseVNode("div", { class: "property-group-title" }, "Secret Options", -1)),
              createBaseVNode("div", _hoisted_63, [
                _cache[66] || (_cache[66] = createBaseVNode("label", { class: "property-label" }, "Required", -1)),
                createBaseVNode("input", {
                  checked: __props.component.required,
                  type: "checkbox",
                  class: "property-checkbox",
                  onChange: _cache[24] || (_cache[24] = ($event) => updateField("required", $event.target.checked))
                }, null, 40, _hoisted_64)
              ]),
              createBaseVNode("div", _hoisted_65, [
                _cache[67] || (_cache[67] = createBaseVNode("label", { class: "property-label" }, "Description", -1)),
                createBaseVNode("input", {
                  value: __props.component.description,
                  type: "text",
                  class: "property-input",
                  placeholder: "Help text for the user",
                  onInput: _cache[25] || (_cache[25] = ($event) => updateField("description", $event.target.value))
                }, null, 40, _hoisted_66)
              ]),
              createBaseVNode("div", _hoisted_67, [
                _cache[68] || (_cache[68] = createBaseVNode("label", { class: "property-label" }, "Name Prefix Filter", -1)),
                createBaseVNode("input", {
                  value: __props.component.name_prefix,
                  type: "text",
                  class: "property-input",
                  placeholder: "e.g. API_KEY_",
                  onInput: _cache[26] || (_cache[26] = ($event) => updateField("name_prefix", $event.target.value))
                }, null, 40, _hoisted_68),
                _cache[69] || (_cache[69] = createBaseVNode("span", { class: "field-hint" }, "Only show secrets starting with this prefix", -1))
              ])
            ])) : createCommentVNode("", true),
            createBaseVNode("div", { class: "action-section" }, [
              createBaseVNode("button", {
                class: "action-btn",
                onClick: insertVariable
              }, [..._cache[71] || (_cache[71] = [
                createBaseVNode("i", { class: "fa-solid fa-code" }, null, -1),
                createTextVNode(" Insert Variable ", -1)
              ])]),
              _cache[72] || (_cache[72] = createBaseVNode("span", { class: "field-hint" }, "Add typed variable to process method", -1))
            ])
          ])) : (openBlock(), createElementBlock("div", _hoisted_69, [..._cache[73] || (_cache[73] = [
            createBaseVNode("i", { class: "fa-solid fa-mouse-pointer" }, null, -1),
            createBaseVNode("p", null, "Select a component to edit its properties", -1)
          ])]))
        ])
      ]);
    };
  }
});
const PropertyEditor = /* @__PURE__ */ _export_sfc(_sfc_main$8, [["__scopeId", "data-v-30942683"]]);
const _hoisted_1$7 = { class: "modal-header" };
const _hoisted_2$7 = { class: "modal-actions" };
const _sfc_main$7 = /* @__PURE__ */ defineComponent({
  __name: "ProcessCodeHelpModal",
  props: {
    show: { type: Boolean }
  },
  emits: ["close"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    return (_ctx, _cache) => {
      return __props.show ? (openBlock(), createElementBlock("div", {
        key: 0,
        class: "modal-overlay",
        onClick: _cache[3] || (_cache[3] = ($event) => emit("close"))
      }, [
        createBaseVNode("div", {
          class: "modal-container modal-large",
          onClick: _cache[2] || (_cache[2] = withModifiers(() => {
          }, ["stop"]))
        }, [
          createBaseVNode("div", _hoisted_1$7, [
            _cache[5] || (_cache[5] = createBaseVNode("h3", { class: "modal-title" }, [
              createBaseVNode("i", { class: "fa-solid fa-circle-question" }),
              createTextVNode(" Process Method Help ")
            ], -1)),
            createBaseVNode("button", {
              class: "modal-close",
              onClick: _cache[0] || (_cache[0] = ($event) => emit("close"))
            }, [..._cache[4] || (_cache[4] = [
              createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
            ])])
          ]),
          _cache[6] || (_cache[6] = createStaticVNode('<div class="modal-content" data-v-3a89a078><div class="help-section" data-v-3a89a078><h4 data-v-3a89a078>Overview</h4><p data-v-3a89a078> The process method is where you write your data transformation logic. It receives input LazyFrames from connected nodes and returns a transformed LazyFrame. </p></div><div class="help-section" data-v-3a89a078><h4 data-v-3a89a078>Method Signature</h4><pre class="help-code" data-v-3a89a078><code data-v-3a89a078>def process(self, *inputs: pl.LazyFrame) -&gt; pl.LazyFrame:</code></pre><ul class="help-list" data-v-3a89a078><li data-v-3a89a078><code data-v-3a89a078>inputs</code> - Tuple of input LazyFrames from connected nodes</li><li data-v-3a89a078><code data-v-3a89a078>inputs[0]</code> - First input (most common)</li><li data-v-3a89a078><code data-v-3a89a078>inputs[1]</code> - Second input (for joins, etc.)</li></ul></div><div class="help-section" data-v-3a89a078><h4 data-v-3a89a078>Accessing Settings</h4><p data-v-3a89a078>Access user-configured values from your UI components:</p><pre class="help-code" data-v-3a89a078><code data-v-3a89a078>self.settings_schema.section_name.component_name.value</code></pre><p class="help-note" data-v-3a89a078><i class="fa-solid fa-lightbulb" data-v-3a89a078></i> Use autocomplete by typing <code data-v-3a89a078>self.</code> to navigate the settings schema. </p></div><div class="help-section" data-v-3a89a078><h4 data-v-3a89a078>Working with Secrets</h4><p data-v-3a89a078>For SecretSelector components, access the decrypted value:</p><pre class="help-code" data-v-3a89a078><code data-v-3a89a078># Get the SecretStr object\nsecret = self.settings_schema.section.api_key.secret_value\n\n# Get the actual decrypted string value\napi_key = secret.get_secret_value()</code></pre></div><div class="help-section" data-v-3a89a078><h4 data-v-3a89a078>Common Patterns</h4><div class="pattern-grid" data-v-3a89a078><div class="pattern-item" data-v-3a89a078><h5 data-v-3a89a078>Filter Rows</h5><pre class="help-code-small" data-v-3a89a078><code data-v-3a89a078>lf = inputs[0]\nreturn lf.filter(pl.col(&quot;column&quot;) &gt; 10)</code></pre></div><div class="pattern-item" data-v-3a89a078><h5 data-v-3a89a078>Select Columns</h5><pre class="help-code-small" data-v-3a89a078><code data-v-3a89a078>lf = inputs[0]\nreturn lf.select([&quot;col1&quot;, &quot;col2&quot;])</code></pre></div><div class="pattern-item" data-v-3a89a078><h5 data-v-3a89a078>Add New Column</h5><pre class="help-code-small" data-v-3a89a078><code data-v-3a89a078>lf = inputs[0]\nreturn lf.with_columns(\n    pl.col(&quot;a&quot;).alias(&quot;new_col&quot;)\n)</code></pre></div><div class="pattern-item" data-v-3a89a078><h5 data-v-3a89a078>Group &amp; Aggregate</h5><pre class="help-code-small" data-v-3a89a078><code data-v-3a89a078>lf = inputs[0]\nreturn lf.group_by(&quot;category&quot;).agg(\n    pl.col(&quot;value&quot;).sum()\n)</code></pre></div></div></div><div class="help-section" data-v-3a89a078><h4 data-v-3a89a078>Using Settings in Code</h4><pre class="help-code" data-v-3a89a078><code data-v-3a89a078># Example: Using a TextInput value\ncolumn_name = self.settings_schema.options.column_name.value\nlf = inputs[0]\nreturn lf.select(pl.col(column_name))\n\n# Example: Using a ColumnSelector value\nselected_columns = self.settings_schema.columns.selected.value\nreturn lf.select(selected_columns)</code></pre></div></div>', 1)),
          createBaseVNode("div", _hoisted_2$7, [
            createBaseVNode("button", {
              class: "btn btn-primary",
              onClick: _cache[1] || (_cache[1] = ($event) => emit("close"))
            }, "Close")
          ])
        ])
      ])) : createCommentVNode("", true);
    };
  }
});
const ProcessCodeHelpModal = /* @__PURE__ */ _export_sfc(_sfc_main$7, [["__scopeId", "data-v-3a89a078"]]);
const _hoisted_1$6 = { class: "code-editor-section" };
const _hoisted_2$6 = { class: "code-editor-header" };
const _hoisted_3$6 = { class: "code-editor-wrapper" };
const _sfc_main$6 = /* @__PURE__ */ defineComponent({
  __name: "ProcessCodeEditor",
  props: {
    modelValue: {},
    extensions: {}
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    const showHelp = ref(false);
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$6, [
        createBaseVNode("div", _hoisted_2$6, [
          _cache[4] || (_cache[4] = createBaseVNode("h4", null, "Process Method", -1)),
          createBaseVNode("button", {
            class: "help-btn",
            title: "Show help",
            onClick: _cache[0] || (_cache[0] = ($event) => showHelp.value = true)
          }, [..._cache[3] || (_cache[3] = [
            createBaseVNode("i", { class: "fa-solid fa-circle-question" }, null, -1),
            createBaseVNode("span", null, "Help", -1)
          ])])
        ]),
        _cache[5] || (_cache[5] = createBaseVNode("p", { class: "code-hint" }, [
          createTextVNode(" Write your data transformation logic. Access settings via "),
          createBaseVNode("code", null, "self.settings_schema.section_name.component_name.value")
        ], -1)),
        createBaseVNode("div", _hoisted_3$6, [
          createVNode(unref(T), {
            "model-value": __props.modelValue,
            placeholder: "# Write your process logic here...",
            style: { height: "300px" },
            autofocus: false,
            "indent-with-tab": false,
            "tab-size": 4,
            extensions: __props.extensions,
            "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => emit("update:modelValue", $event))
          }, null, 8, ["model-value", "extensions"])
        ]),
        createVNode(ProcessCodeHelpModal, {
          show: showHelp.value,
          onClose: _cache[2] || (_cache[2] = ($event) => showHelp.value = false)
        }, null, 8, ["show"])
      ]);
    };
  }
});
const ProcessCodeEditor = /* @__PURE__ */ _export_sfc(_sfc_main$6, [["__scopeId", "data-v-7bd9927f"]]);
const _hoisted_1$5 = { class: "modal-header" };
const _hoisted_2$5 = { class: "modal-content" };
const _hoisted_3$5 = { class: "code-preview" };
const _hoisted_4$5 = { class: "modal-actions" };
const _sfc_main$5 = /* @__PURE__ */ defineComponent({
  __name: "CodePreviewModal",
  props: {
    show: { type: Boolean },
    code: {}
  },
  emits: ["close"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    function copyCode() {
      navigator.clipboard.writeText(arguments[0]);
      alert("Code copied to clipboard!");
    }
    return (_ctx, _cache) => {
      return __props.show ? (openBlock(), createElementBlock("div", {
        key: 0,
        class: "modal-overlay",
        onClick: _cache[3] || (_cache[3] = ($event) => emit("close"))
      }, [
        createBaseVNode("div", {
          class: "modal-container modal-large",
          onClick: _cache[2] || (_cache[2] = withModifiers(() => {
          }, ["stop"]))
        }, [
          createBaseVNode("div", _hoisted_1$5, [
            _cache[5] || (_cache[5] = createBaseVNode("h3", { class: "modal-title" }, "Generated Python Code", -1)),
            createBaseVNode("button", {
              class: "modal-close",
              onClick: _cache[0] || (_cache[0] = ($event) => emit("close"))
            }, [..._cache[4] || (_cache[4] = [
              createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
            ])])
          ]),
          createBaseVNode("div", _hoisted_2$5, [
            createBaseVNode("div", _hoisted_3$5, [
              createBaseVNode("pre", null, [
                createBaseVNode("code", null, toDisplayString(__props.code), 1)
              ])
            ])
          ]),
          createBaseVNode("div", _hoisted_4$5, [
            createBaseVNode("button", {
              class: "btn btn-secondary",
              onClick: copyCode
            }, [..._cache[6] || (_cache[6] = [
              createBaseVNode("i", { class: "fa-solid fa-copy" }, null, -1),
              createTextVNode(" Copy Code ", -1)
            ])]),
            createBaseVNode("button", {
              class: "btn btn-primary",
              onClick: _cache[1] || (_cache[1] = ($event) => emit("close"))
            }, "Close")
          ])
        ])
      ])) : createCommentVNode("", true);
    };
  }
});
const CodePreviewModal = /* @__PURE__ */ _export_sfc(_sfc_main$5, [["__scopeId", "data-v-f74c8de3"]]);
const _hoisted_1$4 = { class: "modal-header modal-header-error" };
const _hoisted_2$4 = { class: "modal-content" };
const _hoisted_3$4 = { class: "validation-errors-list" };
const _hoisted_4$4 = { class: "modal-actions" };
const _sfc_main$4 = /* @__PURE__ */ defineComponent({
  __name: "ValidationModal",
  props: {
    show: { type: Boolean },
    errors: {}
  },
  emits: ["close"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    return (_ctx, _cache) => {
      return __props.show ? (openBlock(), createElementBlock("div", {
        key: 0,
        class: "modal-overlay",
        onClick: _cache[3] || (_cache[3] = ($event) => emit("close"))
      }, [
        createBaseVNode("div", {
          class: "modal-container",
          onClick: _cache[2] || (_cache[2] = withModifiers(() => {
          }, ["stop"]))
        }, [
          createBaseVNode("div", _hoisted_1$4, [
            _cache[5] || (_cache[5] = createBaseVNode("h3", { class: "modal-title" }, [
              createBaseVNode("i", { class: "fa-solid fa-triangle-exclamation" }),
              createTextVNode(" Validation Errors ")
            ], -1)),
            createBaseVNode("button", {
              class: "modal-close",
              onClick: _cache[0] || (_cache[0] = ($event) => emit("close"))
            }, [..._cache[4] || (_cache[4] = [
              createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
            ])])
          ]),
          createBaseVNode("div", _hoisted_2$4, [
            _cache[7] || (_cache[7] = createBaseVNode("p", { class: "validation-intro" }, "Please fix the following issues before saving:", -1)),
            createBaseVNode("ul", _hoisted_3$4, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(__props.errors, (error, index) => {
                return openBlock(), createElementBlock("li", {
                  key: index,
                  class: "validation-error-item"
                }, [
                  _cache[6] || (_cache[6] = createBaseVNode("i", { class: "fa-solid fa-circle-xmark" }, null, -1)),
                  createTextVNode(" " + toDisplayString(error.message), 1)
                ]);
              }), 128))
            ])
          ]),
          createBaseVNode("div", _hoisted_4$4, [
            createBaseVNode("button", {
              class: "btn btn-primary",
              onClick: _cache[1] || (_cache[1] = ($event) => emit("close"))
            }, "OK")
          ])
        ])
      ])) : createCommentVNode("", true);
    };
  }
});
const ValidationModal = /* @__PURE__ */ _export_sfc(_sfc_main$4, [["__scopeId", "data-v-bf9df753"]]);
const _hoisted_1$3 = { class: "modal-header" };
const _hoisted_2$3 = { class: "modal-title" };
const _hoisted_3$3 = { class: "modal-content" };
const _hoisted_4$3 = {
  key: 0,
  class: "node-code-view"
};
const _hoisted_5$3 = {
  key: 0,
  class: "loading-indicator"
};
const _hoisted_6$3 = {
  key: 1,
  class: "empty-nodes"
};
const _hoisted_7$3 = {
  key: 2,
  class: "nodes-grid"
};
const _hoisted_8$3 = ["onClick"];
const _hoisted_9$3 = { class: "node-card-header" };
const _hoisted_10$3 = { class: "node-name" };
const _hoisted_11$3 = { class: "node-card-body" };
const _hoisted_12$2 = { class: "node-category" };
const _hoisted_13$2 = { class: "node-description" };
const _hoisted_14$2 = { class: "node-card-footer" };
const _hoisted_15$2 = { class: "node-file" };
const _hoisted_16$2 = { class: "modal-actions" };
const _hoisted_17$1 = { class: "modal-header modal-header-error" };
const _hoisted_18$1 = { class: "modal-content" };
const _hoisted_19 = { class: "modal-actions" };
const _sfc_main$3 = /* @__PURE__ */ defineComponent({
  __name: "NodeBrowserModal",
  props: {
    show: { type: Boolean },
    nodes: {},
    loading: { type: Boolean },
    viewingNodeCode: {},
    viewingNodeName: {},
    showDeleteConfirm: { type: Boolean },
    readOnlyExtensions: {}
  },
  emits: ["close", "viewNode", "back", "confirmDelete", "cancelDelete", "delete"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock(Fragment, null, [
        __props.show ? (openBlock(), createElementBlock("div", {
          key: 0,
          class: "modal-overlay",
          onClick: _cache[5] || (_cache[5] = ($event) => emit("close"))
        }, [
          createBaseVNode("div", {
            class: "modal-container modal-large",
            onClick: _cache[4] || (_cache[4] = withModifiers(() => {
            }, ["stop"]))
          }, [
            createBaseVNode("div", _hoisted_1$3, [
              createBaseVNode("h3", _hoisted_2$3, [
                _cache[11] || (_cache[11] = createBaseVNode("i", { class: "fa-solid fa-folder-open" }, null, -1)),
                createTextVNode(" " + toDisplayString(__props.viewingNodeCode ? __props.viewingNodeName : "Browse Custom Nodes"), 1)
              ]),
              createBaseVNode("button", {
                class: "modal-close",
                onClick: _cache[0] || (_cache[0] = ($event) => emit("close"))
              }, [..._cache[12] || (_cache[12] = [
                createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
              ])])
            ]),
            createBaseVNode("div", _hoisted_3$3, [
              __props.viewingNodeCode ? (openBlock(), createElementBlock("div", _hoisted_4$3, [
                createVNode(unref(T), {
                  "model-value": __props.viewingNodeCode,
                  style: { height: "auto", maxHeight: "calc(80vh - 180px)" },
                  autofocus: false,
                  "indent-with-tab": false,
                  "tab-size": 4,
                  extensions: __props.readOnlyExtensions
                }, null, 8, ["model-value", "extensions"])
              ])) : (openBlock(), createElementBlock(Fragment, { key: 1 }, [
                __props.loading ? (openBlock(), createElementBlock("div", _hoisted_5$3, [..._cache[13] || (_cache[13] = [
                  createBaseVNode("i", { class: "fa-solid fa-spinner fa-spin" }, null, -1),
                  createTextVNode(" Loading custom nodes... ", -1)
                ])])) : __props.nodes.length === 0 ? (openBlock(), createElementBlock("div", _hoisted_6$3, [..._cache[14] || (_cache[14] = [
                  createBaseVNode("i", { class: "fa-solid fa-folder-open" }, null, -1),
                  createBaseVNode("p", null, "No custom nodes found", -1),
                  createBaseVNode("p", { class: "empty-hint" }, "Save a node to see it here", -1)
                ])])) : (openBlock(), createElementBlock("div", _hoisted_7$3, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList(__props.nodes, (node) => {
                    return openBlock(), createElementBlock("div", {
                      key: node.file_name,
                      class: "node-card",
                      onClick: ($event) => emit("viewNode", node.file_name)
                    }, [
                      createBaseVNode("div", _hoisted_9$3, [
                        _cache[15] || (_cache[15] = createBaseVNode("i", { class: "fa-solid fa-puzzle-piece" }, null, -1)),
                        createBaseVNode("span", _hoisted_10$3, toDisplayString(node.node_name || node.file_name), 1)
                      ]),
                      createBaseVNode("div", _hoisted_11$3, [
                        createBaseVNode("span", _hoisted_12$2, toDisplayString(node.node_category), 1),
                        createBaseVNode("p", _hoisted_13$2, toDisplayString(node.intro || "No description"), 1)
                      ]),
                      createBaseVNode("div", _hoisted_14$2, [
                        createBaseVNode("span", _hoisted_15$2, toDisplayString(node.file_name), 1)
                      ])
                    ], 8, _hoisted_8$3);
                  }), 128))
                ]))
              ], 64))
            ]),
            createBaseVNode("div", _hoisted_16$2, [
              __props.viewingNodeCode ? (openBlock(), createElementBlock("button", {
                key: 0,
                class: "btn btn-secondary",
                onClick: _cache[1] || (_cache[1] = ($event) => emit("back"))
              }, [..._cache[16] || (_cache[16] = [
                createBaseVNode("i", { class: "fa-solid fa-arrow-left" }, null, -1),
                createTextVNode(" Back ", -1)
              ])])) : createCommentVNode("", true),
              __props.viewingNodeCode ? (openBlock(), createElementBlock("button", {
                key: 1,
                class: "btn btn-danger",
                onClick: _cache[2] || (_cache[2] = ($event) => emit("confirmDelete"))
              }, [..._cache[17] || (_cache[17] = [
                createBaseVNode("i", { class: "fa-solid fa-trash" }, null, -1),
                createTextVNode(" Delete ", -1)
              ])])) : createCommentVNode("", true),
              createBaseVNode("button", {
                class: "btn btn-secondary",
                onClick: _cache[3] || (_cache[3] = ($event) => emit("close"))
              }, toDisplayString(__props.viewingNodeCode ? "Close" : "Cancel"), 1)
            ])
          ])
        ])) : createCommentVNode("", true),
        __props.showDeleteConfirm ? (openBlock(), createElementBlock("div", {
          key: 1,
          class: "modal-overlay",
          onClick: _cache[10] || (_cache[10] = ($event) => emit("cancelDelete"))
        }, [
          createBaseVNode("div", {
            class: "modal-container",
            onClick: _cache[9] || (_cache[9] = withModifiers(() => {
            }, ["stop"]))
          }, [
            createBaseVNode("div", _hoisted_17$1, [
              _cache[19] || (_cache[19] = createBaseVNode("h3", { class: "modal-title" }, [
                createBaseVNode("i", { class: "fa-solid fa-triangle-exclamation" }),
                createTextVNode(" Confirm Delete ")
              ], -1)),
              createBaseVNode("button", {
                class: "modal-close",
                onClick: _cache[6] || (_cache[6] = ($event) => emit("cancelDelete"))
              }, [..._cache[18] || (_cache[18] = [
                createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
              ])])
            ]),
            createBaseVNode("div", _hoisted_18$1, [
              createBaseVNode("p", null, [
                _cache[20] || (_cache[20] = createTextVNode(" Are you sure you want to delete ", -1)),
                createBaseVNode("strong", null, toDisplayString(__props.viewingNodeName), 1),
                _cache[21] || (_cache[21] = createTextVNode("? ", -1))
              ]),
              _cache[22] || (_cache[22] = createBaseVNode("p", { class: "delete-warning" }, "This action cannot be undone.", -1))
            ]),
            createBaseVNode("div", _hoisted_19, [
              createBaseVNode("button", {
                class: "btn btn-secondary",
                onClick: _cache[7] || (_cache[7] = ($event) => emit("cancelDelete"))
              }, "Cancel"),
              createBaseVNode("button", {
                class: "btn btn-danger",
                onClick: _cache[8] || (_cache[8] = ($event) => emit("delete"))
              }, [..._cache[23] || (_cache[23] = [
                createBaseVNode("i", { class: "fa-solid fa-trash" }, null, -1),
                createTextVNode(" Delete ", -1)
              ])])
            ])
          ])
        ])) : createCommentVNode("", true)
      ], 64);
    };
  }
});
const NodeBrowserModal = /* @__PURE__ */ _export_sfc(_sfc_main$3, [["__scopeId", "data-v-fca09e8f"]]);
const _hoisted_1$2 = { class: "modal-header" };
const _hoisted_2$2 = { class: "modal-content" };
const _hoisted_3$2 = { class: "help-tabs" };
const _hoisted_4$2 = ["onClick"];
const _hoisted_5$2 = { class: "help-tab-content" };
const _hoisted_6$2 = {
  key: 0,
  class: "tab-panel"
};
const _hoisted_7$2 = {
  key: 1,
  class: "tab-panel"
};
const _hoisted_8$2 = {
  key: 2,
  class: "tab-panel"
};
const _hoisted_9$2 = {
  key: 3,
  class: "tab-panel"
};
const _hoisted_10$2 = {
  key: 4,
  class: "tab-panel"
};
const _hoisted_11$2 = { class: "modal-actions" };
const _sfc_main$2 = /* @__PURE__ */ defineComponent({
  __name: "NodeDesignerHelpModal",
  props: {
    show: { type: Boolean }
  },
  emits: ["close"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    const activeTab = ref("overview");
    const tabs = [
      { id: "overview", label: "Overview", icon: "fa-solid fa-house" },
      { id: "layout", label: "Layout", icon: "fa-solid fa-table-columns" },
      { id: "components", label: "Components", icon: "fa-solid fa-puzzle-piece" },
      { id: "code", label: "Code", icon: "fa-solid fa-code" },
      { id: "tips", label: "Tips", icon: "fa-solid fa-lightbulb" }
    ];
    return (_ctx, _cache) => {
      return __props.show ? (openBlock(), createElementBlock("div", {
        key: 0,
        class: "modal-overlay",
        onClick: _cache[3] || (_cache[3] = ($event) => emit("close"))
      }, [
        createBaseVNode("div", {
          class: "modal-container modal-xl",
          onClick: _cache[2] || (_cache[2] = withModifiers(() => {
          }, ["stop"]))
        }, [
          createBaseVNode("div", _hoisted_1$2, [
            _cache[5] || (_cache[5] = createBaseVNode("h3", { class: "modal-title" }, [
              createBaseVNode("i", { class: "fa-solid fa-circle-question" }),
              createTextVNode(" Node Designer Guide ")
            ], -1)),
            createBaseVNode("button", {
              class: "modal-close",
              onClick: _cache[0] || (_cache[0] = ($event) => emit("close"))
            }, [..._cache[4] || (_cache[4] = [
              createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
            ])])
          ]),
          createBaseVNode("div", _hoisted_2$2, [
            createBaseVNode("div", _hoisted_3$2, [
              (openBlock(), createElementBlock(Fragment, null, renderList(tabs, (tab) => {
                return createBaseVNode("button", {
                  key: tab.id,
                  class: normalizeClass(["help-tab", { active: activeTab.value === tab.id }]),
                  onClick: ($event) => activeTab.value = tab.id
                }, [
                  createBaseVNode("i", {
                    class: normalizeClass(tab.icon)
                  }, null, 2),
                  createTextVNode(" " + toDisplayString(tab.label), 1)
                ], 10, _hoisted_4$2);
              }), 64))
            ]),
            createBaseVNode("div", _hoisted_5$2, [
              activeTab.value === "overview" ? (openBlock(), createElementBlock("div", _hoisted_6$2, [..._cache[6] || (_cache[6] = [
                createStaticVNode('<h4 data-v-865a257f>What is the Node Designer?</h4><p data-v-865a257f> The Node Designer allows you to create custom data transformation nodes without writing boilerplate code. Design your node&#39;s UI visually, then write only the transformation logic. </p><div class="feature-grid" data-v-865a257f><div class="feature-card" data-v-865a257f><div class="feature-icon" data-v-865a257f><i class="fa-solid fa-palette" data-v-865a257f></i></div><h5 data-v-865a257f>Visual UI Design</h5><p data-v-865a257f>Drag and drop components to create your node&#39;s settings interface</p></div><div class="feature-card" data-v-865a257f><div class="feature-icon" data-v-865a257f><i class="fa-solid fa-code" data-v-865a257f></i></div><h5 data-v-865a257f>Python Processing</h5><p data-v-865a257f>Write Polars transformation code with full autocomplete support</p></div><div class="feature-card" data-v-865a257f><div class="feature-icon" data-v-865a257f><i class="fa-solid fa-plug" data-v-865a257f></i></div><h5 data-v-865a257f>Instant Integration</h5><p data-v-865a257f>Your custom nodes appear immediately in the flow editor</p></div></div><h4 data-v-865a257f>Quick Start</h4><ol class="steps-list" data-v-865a257f><li data-v-865a257f><strong data-v-865a257f>Set metadata</strong> - Name your node and choose a category</li><li data-v-865a257f><strong data-v-865a257f>Add sections</strong> - Create UI sections to organize your settings</li><li data-v-865a257f><strong data-v-865a257f>Add components</strong> - Drag components from the palette into sections </li><li data-v-865a257f><strong data-v-865a257f>Configure properties</strong> - Select a component to edit its properties </li><li data-v-865a257f><strong data-v-865a257f>Write process code</strong> - Implement your transformation logic</li><li data-v-865a257f><strong data-v-865a257f>Save</strong> - Your node is ready to use!</li></ol>', 5)
              ])])) : createCommentVNode("", true),
              activeTab.value === "layout" ? (openBlock(), createElementBlock("div", _hoisted_7$2, [..._cache[7] || (_cache[7] = [
                createStaticVNode('<h4 data-v-865a257f>Page Layout</h4><div class="layout-diagram" data-v-865a257f><div class="layout-box palette" data-v-865a257f><span class="layout-label" data-v-865a257f>Component Palette</span><p data-v-865a257f>Drag components from here</p></div><div class="layout-box canvas" data-v-865a257f><span class="layout-label" data-v-865a257f>Design Canvas</span><p data-v-865a257f>Build your node UI here</p></div><div class="layout-box properties" data-v-865a257f><span class="layout-label" data-v-865a257f>Properties</span><p data-v-865a257f>Edit selected component</p></div></div><h4 data-v-865a257f>Component Palette (Left)</h4><p data-v-865a257f> Contains all available UI components. Drag them into a section on the Design Canvas to add them to your node. </p><h4 data-v-865a257f>Design Canvas (Center)</h4><ul class="help-list" data-v-865a257f><li data-v-865a257f><strong data-v-865a257f>Node Metadata</strong> - Set your node&#39;s name, category, title, description, and number of inputs/outputs </li><li data-v-865a257f><strong data-v-865a257f>UI Sections</strong> - Organize your components into collapsible sections </li><li data-v-865a257f><strong data-v-865a257f>Process Method</strong> - Write your Python transformation code</li></ul><h4 data-v-865a257f>Property Editor (Right)</h4><p data-v-865a257f> When you select a component, its properties appear here. Configure labels, defaults, validation rules, and more. </p>', 8)
              ])])) : createCommentVNode("", true),
              activeTab.value === "components" ? (openBlock(), createElementBlock("div", _hoisted_8$2, [..._cache[8] || (_cache[8] = [
                createStaticVNode('<h4 data-v-865a257f>Available Components</h4><div class="component-list" data-v-865a257f><div class="component-item" data-v-865a257f><div class="component-icon" data-v-865a257f><i class="fa-solid fa-font" data-v-865a257f></i></div><div class="component-info" data-v-865a257f><h5 data-v-865a257f>Text Input</h5><p data-v-865a257f>Single-line text entry for strings, names, or patterns</p><code data-v-865a257f>value: str</code></div></div><div class="component-item" data-v-865a257f><div class="component-icon" data-v-865a257f><i class="fa-solid fa-hashtag" data-v-865a257f></i></div><div class="component-info" data-v-865a257f><h5 data-v-865a257f>Numeric Input</h5><p data-v-865a257f>Number entry with optional min/max validation</p><code data-v-865a257f>value: int | float</code></div></div><div class="component-item" data-v-865a257f><div class="component-icon" data-v-865a257f><i class="fa-solid fa-toggle-on" data-v-865a257f></i></div><div class="component-info" data-v-865a257f><h5 data-v-865a257f>Toggle Switch</h5><p data-v-865a257f>Boolean on/off switch for feature flags</p><code data-v-865a257f>value: bool</code></div></div><div class="component-item" data-v-865a257f><div class="component-icon" data-v-865a257f><i class="fa-solid fa-list" data-v-865a257f></i></div><div class="component-info" data-v-865a257f><h5 data-v-865a257f>Single Select</h5><p data-v-865a257f>Dropdown to select one option from a list</p><code data-v-865a257f>value: str</code></div></div><div class="component-item" data-v-865a257f><div class="component-icon" data-v-865a257f><i class="fa-solid fa-list-check" data-v-865a257f></i></div><div class="component-info" data-v-865a257f><h5 data-v-865a257f>Multi Select</h5><p data-v-865a257f>Select multiple options from a list</p><code data-v-865a257f>value: list[str]</code></div></div><div class="component-item" data-v-865a257f><div class="component-icon" data-v-865a257f><i class="fa-solid fa-table-columns" data-v-865a257f></i></div><div class="component-info" data-v-865a257f><h5 data-v-865a257f>Column Selector</h5><p data-v-865a257f>Select columns from input data (single or multiple)</p><code data-v-865a257f>value: str | list[str]</code></div></div><div class="component-item" data-v-865a257f><div class="component-icon" data-v-865a257f><i class="fa-solid fa-sliders" data-v-865a257f></i></div><div class="component-info" data-v-865a257f><h5 data-v-865a257f>Slider</h5><p data-v-865a257f>Numeric slider with min/max/step</p><code data-v-865a257f>value: int | float</code></div></div><div class="component-item" data-v-865a257f><div class="component-icon" data-v-865a257f><i class="fa-solid fa-key" data-v-865a257f></i></div><div class="component-info" data-v-865a257f><h5 data-v-865a257f>Secret Selector</h5><p data-v-865a257f>Securely access stored secrets (API keys, passwords)</p><code data-v-865a257f>secret_value: SecretStr</code></div></div></div>', 2)
              ])])) : createCommentVNode("", true),
              activeTab.value === "code" ? (openBlock(), createElementBlock("div", _hoisted_9$2, [..._cache[9] || (_cache[9] = [
                createStaticVNode('<h4 data-v-865a257f>Process Method</h4><p data-v-865a257f>The process method receives input data and returns transformed output:</p><pre class="help-code" data-v-865a257f><code data-v-865a257f>def process(self, *inputs: pl.LazyFrame) -&gt; pl.LazyFrame:\n    lf = inputs[0]  # First input\n    # Your transformation logic here\n    return lf</code></pre><h4 data-v-865a257f>Accessing Settings</h4><p data-v-865a257f>Access user-configured values from your UI components:</p><pre class="help-code" data-v-865a257f><code data-v-865a257f># Pattern: self.settings_schema.section_name.component_name.value\ncolumn = self.settings_schema.options.column_name.value\nthreshold = self.settings_schema.filters.min_value.value</code></pre><h4 data-v-865a257f>Working with Secrets</h4><pre class="help-code" data-v-865a257f><code data-v-865a257f># Get SecretStr, then extract the actual value\napi_key: SecretStr = self.settings_schema.auth.api_key.secret_value\nactual_key = api_key.get_secret_value()</code></pre><h4 data-v-865a257f>Keyboard Shortcuts</h4><div class="shortcuts-grid" data-v-865a257f><div class="shortcut" data-v-865a257f><kbd data-v-865a257f>Tab</kbd><span data-v-865a257f>Accept autocomplete / Indent</span></div><div class="shortcut" data-v-865a257f><kbd data-v-865a257f>Shift</kbd>+<kbd data-v-865a257f>Tab</kbd><span data-v-865a257f>Outdent selected lines</span></div><div class="shortcut" data-v-865a257f><kbd data-v-865a257f>Arrow Up/Down</kbd><span data-v-865a257f>Navigate autocomplete suggestions</span></div><div class="shortcut" data-v-865a257f><kbd data-v-865a257f>Escape</kbd><span data-v-865a257f>Close autocomplete menu</span></div><div class="shortcut" data-v-865a257f><kbd data-v-865a257f>Shift</kbd>+<kbd data-v-865a257f>Arrow</kbd><span data-v-865a257f>Extend selection</span></div><div class="shortcut" data-v-865a257f><kbd data-v-865a257f>Ctrl</kbd>+<kbd data-v-865a257f>Shift</kbd>+<kbd data-v-865a257f>Arrow</kbd><span data-v-865a257f>Select by word</span></div></div>', 10)
              ])])) : createCommentVNode("", true),
              activeTab.value === "tips" ? (openBlock(), createElementBlock("div", _hoisted_10$2, [..._cache[10] || (_cache[10] = [
                createStaticVNode('<h4 data-v-865a257f>Best Practices</h4><div class="tip-card" data-v-865a257f><div class="tip-icon success" data-v-865a257f><i class="fa-solid fa-check" data-v-865a257f></i></div><div class="tip-content" data-v-865a257f><h5 data-v-865a257f>Use descriptive names</h5><p data-v-865a257f> Choose clear variable names in sections (e.g., &quot;filters&quot;, &quot;options&quot;) and components (e.g., &quot;column_name&quot;, &quot;threshold&quot;) </p></div></div><div class="tip-card" data-v-865a257f><div class="tip-icon success" data-v-865a257f><i class="fa-solid fa-check" data-v-865a257f></i></div><div class="tip-content" data-v-865a257f><h5 data-v-865a257f>Group related settings</h5><p data-v-865a257f> Use sections to organize related components together. This creates a better user experience. </p></div></div><div class="tip-card" data-v-865a257f><div class="tip-icon success" data-v-865a257f><i class="fa-solid fa-check" data-v-865a257f></i></div><div class="tip-content" data-v-865a257f><h5 data-v-865a257f>Use Column Selector for dynamic columns</h5><p data-v-865a257f> Instead of hardcoding column names, use ColumnSelector to let users pick columns from their data. </p></div></div><div class="tip-card" data-v-865a257f><div class="tip-icon warning" data-v-865a257f><i class="fa-solid fa-exclamation" data-v-865a257f></i></div><div class="tip-content" data-v-865a257f><h5 data-v-865a257f>Keep process code simple</h5><p data-v-865a257f> Focus on transformation logic. Complex operations should be broken into multiple nodes. </p></div></div><div class="tip-card" data-v-865a257f><div class="tip-icon warning" data-v-865a257f><i class="fa-solid fa-exclamation" data-v-865a257f></i></div><div class="tip-content" data-v-865a257f><h5 data-v-865a257f>Use secrets for sensitive data</h5><p data-v-865a257f> Never hardcode API keys or passwords. Use the Secret Selector component for secure credential access. </p></div></div><h4 data-v-865a257f>Common Patterns</h4><pre class="help-code" data-v-865a257f><code data-v-865a257f># Filter rows\nreturn lf.filter(pl.col(column) &gt; threshold)\n\n# Select and rename\nreturn lf.select([\n    pl.col(old_name).alias(new_name)\n])\n\n# Add computed column\nreturn lf.with_columns(\n    (pl.col(&quot;a&quot;) + pl.col(&quot;b&quot;)).alias(&quot;sum&quot;)\n)\n\n# Group and aggregate\nreturn lf.group_by(group_col).agg(\n    pl.col(value_col).sum().alias(&quot;total&quot;)\n)</code></pre>', 8)
              ])])) : createCommentVNode("", true)
            ])
          ]),
          createBaseVNode("div", _hoisted_11$2, [
            createBaseVNode("button", {
              class: "btn btn-primary",
              onClick: _cache[1] || (_cache[1] = ($event) => emit("close"))
            }, "Close")
          ])
        ])
      ])) : createCommentVNode("", true);
    };
  }
});
const NodeDesignerHelpModal = /* @__PURE__ */ _export_sfc(_sfc_main$2, [["__scopeId", "data-v-865a257f"]]);
const _hoisted_1$1 = { class: "icon-selector" };
const _hoisted_2$1 = { class: "icon-selector-content" };
const _hoisted_3$1 = ["src", "alt"];
const _hoisted_4$1 = { class: "icon-name" };
const _hoisted_5$1 = {
  key: 0,
  class: "icon-dropdown"
};
const _hoisted_6$1 = { class: "upload-section" };
const _hoisted_7$1 = { class: "upload-btn" };
const _hoisted_8$1 = {
  key: 0,
  class: "icons-section"
};
const _hoisted_9$1 = { class: "icons-grid" };
const _hoisted_10$1 = ["onClick"];
const _hoisted_11$1 = ["src", "alt"];
const _hoisted_12$1 = { class: "icon-filename" };
const _hoisted_13$1 = ["onClick"];
const _hoisted_14$1 = { class: "icons-section" };
const _hoisted_15$1 = { class: "icons-grid" };
const _hoisted_16$1 = ["src"];
const _sfc_main$1 = /* @__PURE__ */ defineComponent({
  __name: "IconSelector",
  props: {
    modelValue: {}
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const showDropdown = ref(false);
    const customIcons = ref([]);
    const loading = ref(false);
    function toggleDropdown() {
      showDropdown.value = !showDropdown.value;
      if (showDropdown.value) {
        loadIcons();
      }
    }
    async function loadIcons() {
      loading.value = true;
      try {
        const response = await axios.get("/user_defined_components/list-icons");
        customIcons.value = response.data;
      } catch (error) {
        console.error("Failed to load icons:", error);
      } finally {
        loading.value = false;
      }
    }
    function selectIcon(iconName) {
      emit("update:modelValue", iconName);
      showDropdown.value = false;
    }
    async function handleFileUpload(event) {
      var _a, _b, _c;
      const target = event.target;
      const file = (_a = target.files) == null ? void 0 : _a[0];
      if (!file) return;
      const formData = new FormData();
      formData.append("file", file);
      try {
        const response = await axios.post("/user_defined_components/upload-icon", formData, {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        });
        emit("update:modelValue", response.data.file_name);
        await loadIcons();
      } catch (error) {
        const errorMsg = ((_c = (_b = error.response) == null ? void 0 : _b.data) == null ? void 0 : _c.detail) || error.message || "Failed to upload icon";
        alert(`Error uploading icon: ${errorMsg}`);
      }
      target.value = "";
    }
    async function deleteIcon(iconName) {
      var _a, _b;
      if (!confirm(`Are you sure you want to delete "${iconName}"?`)) return;
      try {
        await axios.delete(`/user_defined_components/delete-icon/${iconName}`);
        if (props.modelValue === iconName) {
          emit("update:modelValue", "user-defined-icon.png");
        }
        await loadIcons();
      } catch (error) {
        const errorMsg = ((_b = (_a = error.response) == null ? void 0 : _a.data) == null ? void 0 : _b.detail) || error.message || "Failed to delete icon";
        alert(`Error deleting icon: ${errorMsg}`);
      }
    }
    function getDisplayUrl(iconName) {
      return getImageUrl(iconName);
    }
    function getCustomIconUrl$1(iconName) {
      return getCustomIconUrl(iconName);
    }
    function getBuiltinIconUrl(iconName) {
      return new URL((/* @__PURE__ */ Object.assign({ "../../features/designer/assets/icons/Output2.png": __vite_glob_0_0, "../../features/designer/assets/icons/airbyte.png": __vite_glob_0_1, "../../features/designer/assets/icons/cloud_storage_reader.png": __vite_glob_0_2, "../../features/designer/assets/icons/cloud_storage_writer.png": __vite_glob_0_3, "../../features/designer/assets/icons/cross_join.png": __vite_glob_0_4, "../../features/designer/assets/icons/database_reader.svg": __vite_glob_0_5, "../../features/designer/assets/icons/database_writer.svg": __vite_glob_0_6, "../../features/designer/assets/icons/explore_data.png": __vite_glob_0_7, "../../features/designer/assets/icons/external_source.png": __vite_glob_0_8, "../../features/designer/assets/icons/filter.png": __vite_glob_0_9, "../../features/designer/assets/icons/formula.png": __vite_glob_0_10, "../../features/designer/assets/icons/fuzzy_match.png": __vite_glob_0_11, "../../features/designer/assets/icons/google_sheet.png": __vite_glob_0_12, "../../features/designer/assets/icons/graph_solver.png": __vite_glob_0_13, "../../features/designer/assets/icons/group_by.png": __vite_glob_0_14, "../../features/designer/assets/icons/input_data.png": __vite_glob_0_15, "../../features/designer/assets/icons/join.png": __vite_glob_0_16, "../../features/designer/assets/icons/manual_input.png": __vite_glob_0_17, "../../features/designer/assets/icons/old_join.png": __vite_glob_0_18, "../../features/designer/assets/icons/output.png": __vite_glob_0_19, "../../features/designer/assets/icons/pivot.png": __vite_glob_0_20, "../../features/designer/assets/icons/polars_code.png": __vite_glob_0_21, "../../features/designer/assets/icons/record_count.png": __vite_glob_0_22, "../../features/designer/assets/icons/record_id.png": __vite_glob_0_23, "../../features/designer/assets/icons/sample.png": __vite_glob_0_24, "../../features/designer/assets/icons/select.png": __vite_glob_0_25, "../../features/designer/assets/icons/sort.png": __vite_glob_0_26, "../../features/designer/assets/icons/summarize.png": __vite_glob_0_27, "../../features/designer/assets/icons/text_to_rows.png": __vite_glob_0_28, "../../features/designer/assets/icons/union.png": __vite_glob_0_29, "../../features/designer/assets/icons/unique.png": __vite_glob_0_30, "../../features/designer/assets/icons/unpivot.png": __vite_glob_0_31, "../../features/designer/assets/icons/user-defined-icon.png": __vite_glob_0_32, "../../features/designer/assets/icons/view.png": __vite_glob_0_33 }))[`../../features/designer/assets/icons/${iconName}`], import.meta.url).href;
    }
    function handleImageError(event) {
      const img = event.target;
      img.src = getDefaultIconUrl();
    }
    onMounted(() => {
      loadIcons();
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$1, [
        _cache[9] || (_cache[9] = createBaseVNode("label", { class: "icon-label" }, "Node Icon", -1)),
        createBaseVNode("div", _hoisted_2$1, [
          createBaseVNode("div", {
            class: "current-icon",
            onClick: toggleDropdown
          }, [
            createBaseVNode("img", {
              src: getDisplayUrl(__props.modelValue),
              alt: __props.modelValue,
              class: "icon-preview",
              onError: handleImageError
            }, null, 40, _hoisted_3$1),
            createBaseVNode("span", _hoisted_4$1, toDisplayString(__props.modelValue || "Select icon..."), 1),
            _cache[2] || (_cache[2] = createBaseVNode("i", { class: "fa-solid fa-chevron-down dropdown-arrow" }, null, -1))
          ]),
          showDropdown.value ? (openBlock(), createElementBlock("div", _hoisted_5$1, [
            createBaseVNode("div", _hoisted_6$1, [
              createBaseVNode("label", _hoisted_7$1, [
                _cache[3] || (_cache[3] = createBaseVNode("i", { class: "fa-solid fa-upload" }, null, -1)),
                _cache[4] || (_cache[4] = createTextVNode(" Upload Icon ", -1)),
                createBaseVNode("input", {
                  type: "file",
                  accept: ".png,.jpg,.jpeg,.svg,.gif,.webp",
                  hidden: "",
                  onChange: handleFileUpload
                }, null, 32)
              ])
            ]),
            customIcons.value.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_8$1, [
              _cache[6] || (_cache[6] = createBaseVNode("div", { class: "section-title" }, "Custom Icons", -1)),
              createBaseVNode("div", _hoisted_9$1, [
                (openBlock(true), createElementBlock(Fragment, null, renderList(customIcons.value, (icon) => {
                  return openBlock(), createElementBlock("div", {
                    key: icon.file_name,
                    class: normalizeClass(["icon-option", { selected: __props.modelValue === icon.file_name }]),
                    onClick: ($event) => selectIcon(icon.file_name)
                  }, [
                    createBaseVNode("img", {
                      src: getCustomIconUrl$1(icon.file_name),
                      alt: icon.file_name,
                      class: "icon-img",
                      onError: handleImageError
                    }, null, 40, _hoisted_11$1),
                    createBaseVNode("span", _hoisted_12$1, toDisplayString(icon.file_name), 1),
                    createBaseVNode("button", {
                      class: "delete-icon-btn",
                      title: "Delete icon",
                      onClick: withModifiers(($event) => deleteIcon(icon.file_name), ["stop"])
                    }, [..._cache[5] || (_cache[5] = [
                      createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
                    ])], 8, _hoisted_13$1)
                  ], 10, _hoisted_10$1);
                }), 128))
              ])
            ])) : createCommentVNode("", true),
            createBaseVNode("div", _hoisted_14$1, [
              _cache[8] || (_cache[8] = createBaseVNode("div", { class: "section-title" }, "Default", -1)),
              createBaseVNode("div", _hoisted_15$1, [
                createBaseVNode("div", {
                  class: normalizeClass(["icon-option", { selected: __props.modelValue === "user-defined-icon.png" }]),
                  onClick: _cache[0] || (_cache[0] = ($event) => selectIcon("user-defined-icon.png"))
                }, [
                  createBaseVNode("img", {
                    src: getBuiltinIconUrl("user-defined-icon.png"),
                    alt: "Default",
                    class: "icon-img"
                  }, null, 8, _hoisted_16$1),
                  _cache[7] || (_cache[7] = createBaseVNode("span", { class: "icon-filename" }, "Default", -1))
                ], 2)
              ])
            ])
          ])) : createCommentVNode("", true)
        ]),
        showDropdown.value ? (openBlock(), createElementBlock("div", {
          key: 0,
          class: "backdrop",
          onClick: _cache[1] || (_cache[1] = ($event) => showDropdown.value = false)
        })) : createCommentVNode("", true)
      ]);
    };
  }
});
const IconSelector = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["__scopeId", "data-v-24b16154"]]);
function useNodeDesignerState() {
  const nodeMetadata = reactive({ ...defaultNodeMetadata });
  const sections = ref([]);
  const selectedSectionIndex = ref(null);
  const selectedComponentIndex = ref(null);
  const processCode = ref(defaultProcessCode);
  const selectedComponent = computed(() => {
    var _a;
    if (selectedSectionIndex.value !== null && selectedComponentIndex.value !== null) {
      return ((_a = sections.value[selectedSectionIndex.value]) == null ? void 0 : _a.components[selectedComponentIndex.value]) || null;
    }
    return null;
  });
  const canSave = computed(() => {
    return nodeMetadata.node_name.trim() !== "" && nodeMetadata.node_category.trim() !== "";
  });
  function addSection() {
    const sectionNumber = sections.value.length + 1;
    sections.value.push({
      name: `section_${sectionNumber}`,
      title: `Section ${sectionNumber}`,
      components: []
    });
    selectedSectionIndex.value = sections.value.length - 1;
    selectedComponentIndex.value = null;
  }
  function removeSection(index) {
    sections.value.splice(index, 1);
    if (selectedSectionIndex.value === index) {
      selectedSectionIndex.value = null;
      selectedComponentIndex.value = null;
    }
  }
  function selectSection(index) {
    selectedSectionIndex.value = index;
    selectedComponentIndex.value = null;
  }
  function sanitizeSectionName(index) {
    let name = sections.value[index].name;
    name = name.replace(/[\s-]+/g, "_");
    name = name.replace(/[^a-zA-Z0-9_]/g, "");
    if (/^[0-9]/.test(name)) {
      name = "_" + name;
    }
    name = name.toLowerCase();
    sections.value[index].name = name;
  }
  function selectComponent(sectionIndex, compIndex) {
    selectedSectionIndex.value = sectionIndex;
    selectedComponentIndex.value = compIndex;
  }
  function removeComponent(sectionIndex, compIndex) {
    sections.value[sectionIndex].components.splice(compIndex, 1);
    if (selectedSectionIndex.value === sectionIndex && selectedComponentIndex.value === compIndex) {
      selectedComponentIndex.value = null;
    }
  }
  function addComponentToSection(sectionIndex, component) {
    sections.value[sectionIndex].components.push(component);
    selectedSectionIndex.value = sectionIndex;
    selectedComponentIndex.value = sections.value[sectionIndex].components.length - 1;
  }
  function resetState() {
    Object.assign(nodeMetadata, defaultNodeMetadata);
    sections.value = [];
    processCode.value = defaultProcessCode;
    selectedSectionIndex.value = null;
    selectedComponentIndex.value = null;
  }
  function getState() {
    return {
      nodeMetadata: { ...nodeMetadata },
      sections: sections.value,
      processCode: processCode.value
    };
  }
  function setState(state) {
    if (state.nodeMetadata) {
      Object.assign(nodeMetadata, state.nodeMetadata);
    }
    if (state.sections) {
      sections.value = state.sections;
    }
    if (state.processCode) {
      processCode.value = state.processCode;
    }
  }
  return {
    // State
    nodeMetadata,
    sections,
    selectedSectionIndex,
    selectedComponentIndex,
    processCode,
    // Computed
    selectedComponent,
    canSave,
    // Section methods
    addSection,
    removeSection,
    selectSection,
    sanitizeSectionName,
    // Component methods
    selectComponent,
    removeComponent,
    addComponentToSection,
    // State management
    resetState,
    getState,
    setState
  };
}
function useSessionStorage(getState, setState, resetState) {
  function saveToSessionStorage() {
    const state = getState();
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }
  function loadFromSessionStorage() {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const state = JSON.parse(saved);
        setState(state);
      } catch (e) {
        console.error("Failed to load from session storage:", e);
      }
    }
  }
  function clearSessionStorage() {
    sessionStorage.removeItem(STORAGE_KEY);
    resetState();
  }
  function setupAutoSave(watchSources) {
    watch(
      watchSources,
      () => {
        saveToSessionStorage();
      },
      { deep: true }
    );
  }
  function setupLoadOnMount() {
    onMounted(() => {
      loadFromSessionStorage();
    });
  }
  return {
    saveToSessionStorage,
    loadFromSessionStorage,
    clearSessionStorage,
    setupAutoSave,
    setupLoadOnMount
  };
}
function useNodeValidation() {
  const validationErrors = ref([]);
  const showValidationModal = ref(false);
  function validateSettings(nodeMetadata, sections, processCode) {
    const errors = [];
    if (!nodeMetadata.node_name.trim()) {
      errors.push({ field: "node_name", message: "Node name is required" });
    } else if (!/^[a-zA-Z][a-zA-Z0-9_\s]*$/.test(nodeMetadata.node_name)) {
      errors.push({
        field: "node_name",
        message: "Node name must start with a letter and contain only letters, numbers, spaces, and underscores"
      });
    }
    if (!nodeMetadata.node_category.trim()) {
      errors.push({ field: "node_category", message: "Category is required" });
    }
    const sectionNames = /* @__PURE__ */ new Set();
    sections.forEach((section, index) => {
      const name = section.name || toSnakeCase(section.title || "section");
      if (sectionNames.has(name)) {
        errors.push({ field: `section_${index}`, message: `Duplicate section name: "${name}"` });
      }
      sectionNames.add(name);
      const fieldNames = /* @__PURE__ */ new Set();
      section.components.forEach((comp, compIndex) => {
        const fieldName = toSnakeCase(comp.field_name);
        if (!fieldName) {
          errors.push({
            field: `section_${index}_comp_${compIndex}`,
            message: `Component in "${section.title}" is missing a field name`
          });
        } else if (fieldNames.has(fieldName)) {
          errors.push({
            field: `section_${index}_comp_${compIndex}`,
            message: `Duplicate field name "${fieldName}" in section "${section.title}"`
          });
        }
        fieldNames.add(fieldName);
      });
    });
    if (!processCode.includes("def process")) {
      errors.push({ field: "process_code", message: "Process method definition is missing" });
    }
    if (!processCode.includes("return")) {
      errors.push({ field: "process_code", message: "Process method must return a value" });
    }
    return errors;
  }
  function showErrors(errors) {
    validationErrors.value = errors;
    showValidationModal.value = true;
  }
  function closeValidationModal() {
    showValidationModal.value = false;
  }
  return {
    validationErrors,
    showValidationModal,
    validateSettings,
    showErrors,
    closeValidationModal
  };
}
function useNodeBrowser() {
  const showNodeBrowser = ref(false);
  const customNodes = ref([]);
  const loadingNodes = ref(false);
  const viewingNodeCode = ref("");
  const viewingNodeName = ref("");
  const viewingNodeFileName = ref("");
  const showDeleteConfirm = ref(false);
  async function fetchCustomNodes() {
    loadingNodes.value = true;
    try {
      const response = await axios.get("/user_defined_components/list-custom-nodes");
      customNodes.value = response.data;
    } catch (error) {
      console.error("Failed to fetch custom nodes:", error);
      customNodes.value = [];
    } finally {
      loadingNodes.value = false;
    }
  }
  async function viewCustomNode(fileName) {
    var _a;
    try {
      const response = await axios.get(`/user_defined_components/get-custom-node/${fileName}`);
      const nodeData = response.data;
      viewingNodeFileName.value = fileName;
      viewingNodeName.value = ((_a = nodeData.metadata) == null ? void 0 : _a.node_name) || fileName;
      viewingNodeCode.value = nodeData.content || "// No content available";
    } catch (error) {
      console.error("Failed to load custom node:", error);
      viewingNodeCode.value = `// Error loading node: ${error.message || "Unknown error"}`;
    }
  }
  function openNodeBrowser() {
    fetchCustomNodes();
    viewingNodeCode.value = "";
    viewingNodeName.value = "";
    viewingNodeFileName.value = "";
    showNodeBrowser.value = true;
  }
  function closeNodeBrowser() {
    showNodeBrowser.value = false;
    viewingNodeCode.value = "";
    viewingNodeName.value = "";
    viewingNodeFileName.value = "";
  }
  function backToNodeList() {
    viewingNodeCode.value = "";
    viewingNodeName.value = "";
    viewingNodeFileName.value = "";
  }
  function confirmDeleteNode() {
    showDeleteConfirm.value = true;
  }
  async function deleteNode() {
    var _a, _b;
    if (!viewingNodeFileName.value) return;
    try {
      await axios.delete(
        `/user_defined_components/delete-custom-node/${viewingNodeFileName.value}`
      );
      showDeleteConfirm.value = false;
      backToNodeList();
      fetchCustomNodes();
    } catch (error) {
      console.error("Failed to delete custom node:", error);
      alert(
        `Error deleting node: ${((_b = (_a = error.response) == null ? void 0 : _a.data) == null ? void 0 : _b.detail) || error.message || "Unknown error"}`
      );
      showDeleteConfirm.value = false;
    }
  }
  return {
    // State
    showNodeBrowser,
    customNodes,
    loadingNodes,
    viewingNodeCode,
    viewingNodeName,
    viewingNodeFileName,
    showDeleteConfirm,
    // Methods
    fetchCustomNodes,
    viewCustomNode,
    openNodeBrowser,
    closeNodeBrowser,
    backToNodeList,
    confirmDeleteNode,
    deleteNode
  };
}
const lazyFrameMethods = [
  // Selection & Filtering
  { label: "select", type: "method", info: "Select columns", apply: "select()" },
  { label: "filter", type: "method", info: "Filter rows by condition", apply: "filter()" },
  { label: "with_columns", type: "method", info: "Add or modify columns", apply: "with_columns()" },
  { label: "drop", type: "method", info: "Drop columns", apply: "drop()" },
  { label: "rename", type: "method", info: "Rename columns", apply: "rename({})" },
  { label: "cast", type: "method", info: "Cast column types", apply: "cast({})" },
  // Sorting & Limiting
  { label: "sort", type: "method", info: "Sort by columns", apply: 'sort("")' },
  { label: "head", type: "method", info: "Get first n rows", apply: "head()" },
  { label: "tail", type: "method", info: "Get last n rows", apply: "tail()" },
  { label: "limit", type: "method", info: "Limit number of rows", apply: "limit()" },
  { label: "slice", type: "method", info: "Slice rows by offset and length", apply: "slice()" },
  { label: "unique", type: "method", info: "Get unique rows", apply: "unique()" },
  // Grouping & Aggregation
  { label: "group_by", type: "method", info: "Group by columns", apply: "group_by().agg()" },
  { label: "agg", type: "method", info: "Aggregate expressions", apply: "agg()" },
  { label: "rolling", type: "method", info: "Rolling window operations", apply: "rolling()" },
  {
    label: "group_by_dynamic",
    type: "method",
    info: "Dynamic time-based grouping",
    apply: "group_by_dynamic()"
  },
  // Joins
  {
    label: "join",
    type: "method",
    info: "Join with another LazyFrame",
    apply: 'join(other, on="", how="left")'
  },
  { label: "join_asof", type: "method", info: "As-of join for time series", apply: "join_asof()" },
  {
    label: "cross_join",
    type: "method",
    info: "Cross join (cartesian product)",
    apply: "cross_join()"
  },
  // Reshaping
  { label: "explode", type: "method", info: "Explode list column to rows", apply: 'explode("")' },
  { label: "unpivot", type: "method", info: "Unpivot wide to long format", apply: "unpivot()" },
  { label: "pivot", type: "method", info: "Pivot long to wide format", apply: "pivot()" },
  { label: "unnest", type: "method", info: "Unnest struct column", apply: 'unnest("")' },
  // Missing data
  { label: "fill_null", type: "method", info: "Fill null values", apply: "fill_null()" },
  { label: "fill_nan", type: "method", info: "Fill NaN values", apply: "fill_nan()" },
  { label: "drop_nulls", type: "method", info: "Drop rows with nulls", apply: "drop_nulls()" },
  { label: "interpolate", type: "method", info: "Interpolate null values", apply: "interpolate()" },
  // Other
  {
    label: "with_row_index",
    type: "method",
    info: "Add row index column",
    apply: 'with_row_index("index")'
  },
  { label: "reverse", type: "method", info: "Reverse row order", apply: "reverse()" },
  {
    label: "collect",
    type: "method",
    info: "Execute and collect to DataFrame",
    apply: "collect()"
  },
  { label: "lazy", type: "method", info: "Convert to LazyFrame", apply: "lazy()" },
  // Expression methods (chainable)
  { label: "alias", type: "method", info: "Rename expression result", apply: 'alias("")' },
  { label: "is_null", type: "method", info: "Check for null", apply: "is_null()" },
  { label: "is_not_null", type: "method", info: "Check for not null", apply: "is_not_null()" },
  { label: "sum", type: "method", info: "Sum values", apply: "sum()" },
  { label: "mean", type: "method", info: "Calculate mean", apply: "mean()" },
  { label: "min", type: "method", info: "Get minimum", apply: "min()" },
  { label: "max", type: "method", info: "Get maximum", apply: "max()" },
  { label: "count", type: "method", info: "Count values", apply: "count()" },
  { label: "first", type: "method", info: "Get first value", apply: "first()" },
  { label: "last", type: "method", info: "Get last value", apply: "last()" },
  { label: "str", type: "property", info: "String operations namespace", apply: "str." },
  { label: "dt", type: "property", info: "Datetime operations namespace", apply: "dt." },
  { label: "list", type: "property", info: "List operations namespace", apply: "list." },
  { label: "over", type: "method", info: "Window function over groups", apply: 'over("")' }
];
const polarsCompletions = [
  { label: "self", type: "keyword", info: "Access node instance" },
  { label: "inputs[0]", type: "variable", info: "First input LazyFrame" },
  { label: "inputs[1]", type: "variable", info: "Second input LazyFrame" },
  // Polars expressions
  { label: "pl.col", type: "function", info: "Select a column by name", apply: 'pl.col("")' },
  { label: "pl.lit", type: "function", info: "Create a literal value", apply: "pl.lit()" },
  { label: "pl.all", type: "function", info: "Select all columns", apply: "pl.all()" },
  {
    label: "pl.exclude",
    type: "function",
    info: "Select all except specified",
    apply: 'pl.exclude("")'
  },
  {
    label: "pl.when",
    type: "function",
    info: "Start conditional expression",
    apply: "pl.when().then().otherwise()"
  },
  { label: "pl.concat", type: "function", info: "Concatenate LazyFrames", apply: "pl.concat([])" },
  { label: "pl.struct", type: "function", info: "Create struct column", apply: "pl.struct([])" },
  // LazyFrame methods with lf. prefix
  { label: "lf.select", type: "method", info: "Select columns", apply: "lf.select()" },
  { label: "lf.filter", type: "method", info: "Filter rows by condition", apply: "lf.filter()" },
  {
    label: "lf.with_columns",
    type: "method",
    info: "Add or modify columns",
    apply: "lf.with_columns()"
  },
  { label: "lf.drop", type: "method", info: "Drop columns", apply: "lf.drop()" },
  { label: "lf.rename", type: "method", info: "Rename columns", apply: "lf.rename({})" },
  { label: "lf.cast", type: "method", info: "Cast column types", apply: "lf.cast({})" },
  { label: "lf.sort", type: "method", info: "Sort by columns", apply: 'lf.sort("")' },
  { label: "lf.head", type: "method", info: "Get first n rows", apply: "lf.head()" },
  { label: "lf.tail", type: "method", info: "Get last n rows", apply: "lf.tail()" },
  { label: "lf.limit", type: "method", info: "Limit number of rows", apply: "lf.limit()" },
  {
    label: "lf.slice",
    type: "method",
    info: "Slice rows by offset and length",
    apply: "lf.slice()"
  },
  { label: "lf.unique", type: "method", info: "Get unique rows", apply: "lf.unique()" },
  { label: "lf.group_by", type: "method", info: "Group by columns", apply: "lf.group_by().agg()" },
  { label: "lf.agg", type: "method", info: "Aggregate expressions", apply: "lf.agg()" },
  { label: "lf.rolling", type: "method", info: "Rolling window operations", apply: "lf.rolling()" },
  {
    label: "lf.group_by_dynamic",
    type: "method",
    info: "Dynamic time-based grouping",
    apply: "lf.group_by_dynamic()"
  },
  {
    label: "lf.join",
    type: "method",
    info: "Join with another LazyFrame",
    apply: 'lf.join(other, on="", how="left")'
  },
  {
    label: "lf.join_asof",
    type: "method",
    info: "As-of join for time series",
    apply: "lf.join_asof()"
  },
  {
    label: "lf.cross_join",
    type: "method",
    info: "Cross join (cartesian product)",
    apply: "lf.cross_join()"
  },
  {
    label: "lf.explode",
    type: "method",
    info: "Explode list column to rows",
    apply: 'lf.explode("")'
  },
  {
    label: "lf.unpivot",
    type: "method",
    info: "Unpivot wide to long format",
    apply: "lf.unpivot()"
  },
  { label: "lf.pivot", type: "method", info: "Pivot long to wide format", apply: "lf.pivot()" },
  { label: "lf.unnest", type: "method", info: "Unnest struct column", apply: 'lf.unnest("")' },
  { label: "lf.fill_null", type: "method", info: "Fill null values", apply: "lf.fill_null()" },
  { label: "lf.fill_nan", type: "method", info: "Fill NaN values", apply: "lf.fill_nan()" },
  {
    label: "lf.drop_nulls",
    type: "method",
    info: "Drop rows with nulls",
    apply: "lf.drop_nulls()"
  },
  {
    label: "lf.interpolate",
    type: "method",
    info: "Interpolate null values",
    apply: "lf.interpolate()"
  },
  {
    label: "lf.with_row_index",
    type: "method",
    info: "Add row index column",
    apply: 'lf.with_row_index("index")'
  },
  { label: "lf.reverse", type: "method", info: "Reverse row order", apply: "lf.reverse()" },
  {
    label: "lf.collect",
    type: "method",
    info: "Execute and collect to DataFrame",
    apply: "lf.collect()"
  },
  { label: "lf.lazy", type: "method", info: "Convert to LazyFrame", apply: "lf.lazy()" },
  // Expression methods
  { label: ".alias", type: "method", info: "Rename expression result", apply: '.alias("")' },
  { label: ".cast", type: "method", info: "Cast to type", apply: ".cast(pl.Utf8)" },
  { label: ".is_null", type: "method", info: "Check for null", apply: ".is_null()" },
  { label: ".is_not_null", type: "method", info: "Check for not null", apply: ".is_not_null()" },
  { label: ".fill_null", type: "method", info: "Fill null values", apply: ".fill_null()" },
  { label: ".sum", type: "method", info: "Sum values", apply: ".sum()" },
  { label: ".mean", type: "method", info: "Calculate mean", apply: ".mean()" },
  { label: ".min", type: "method", info: "Get minimum", apply: ".min()" },
  { label: ".max", type: "method", info: "Get maximum", apply: ".max()" },
  { label: ".count", type: "method", info: "Count values", apply: ".count()" },
  { label: ".first", type: "method", info: "Get first value", apply: ".first()" },
  { label: ".last", type: "method", info: "Get last value", apply: ".last()" },
  { label: ".str", type: "property", info: "String operations namespace", apply: ".str." },
  { label: ".dt", type: "property", info: "Datetime operations namespace", apply: ".dt." },
  { label: ".list", type: "property", info: "List operations namespace", apply: ".list." },
  { label: ".over", type: "method", info: "Window function over groups", apply: '.over("")' }
];
const secretStrMethods = [
  {
    label: "get_secret_value",
    type: "method",
    info: "Get the decrypted secret value as a string",
    apply: "get_secret_value()",
    detail: "SecretStr"
  }
];
function usePolarsAutocompletion(getSections) {
  function findSecretStrVariables(doc) {
    const variables = [];
    const typeAnnotationPattern = /(\w+)\s*:\s*SecretStr\s*=/g;
    let match;
    while ((match = typeAnnotationPattern.exec(doc)) !== null) {
      variables.push(match[1]);
    }
    return variables;
  }
  function schemaCompletions(context) {
    const beforeCursor = context.state.doc.sliceString(0, context.pos);
    const fullDoc = context.state.doc.toString();
    const sections = getSections();
    const secretStrVars = findSecretStrVariables(fullDoc);
    for (const varName of secretStrVars) {
      const varMethodMatch = beforeCursor.match(new RegExp(`\\b${varName}\\.(\\w*)$`));
      if (varMethodMatch) {
        const typed = varMethodMatch[1];
        return {
          from: context.pos - typed.length,
          options: secretStrMethods,
          validFor: /^\w*$/
        };
      }
    }
    const secretStrMethodMatch = beforeCursor.match(/\.secret_value\.(\w*)$/);
    if (secretStrMethodMatch) {
      const typed = secretStrMethodMatch[1];
      return {
        from: context.pos - typed.length,
        options: secretStrMethods,
        validFor: /^\w*$/
      };
    }
    for (const section of sections) {
      const sectionName = section.name || toSnakeCase(section.title || "section");
      for (const comp of section.components) {
        const fieldName = toSnakeCase(comp.field_name);
        const valueMatch = beforeCursor.match(
          new RegExp(`self\\.settings_schema\\.${sectionName}\\.${fieldName}\\.(\\w*)$`)
        );
        if (valueMatch) {
          const typed = valueMatch[1];
          if (comp.component_type === "SecretSelector") {
            return {
              from: context.pos - typed.length,
              options: [
                {
                  label: "secret_value",
                  type: "property",
                  info: "Get the decrypted secret value (SecretStr)",
                  detail: "SecretSelector"
                }
              ],
              validFor: /^\w*$/
            };
          }
          return {
            from: context.pos - typed.length,
            options: [
              {
                label: "value",
                type: "property",
                info: "Get the setting value",
                detail: comp.component_type
              }
            ],
            validFor: /^\w*$/
          };
        }
      }
    }
    for (const section of sections) {
      const sectionName = section.name || toSnakeCase(section.title || "section");
      const sectionMatch = beforeCursor.match(
        new RegExp(`self\\.settings_schema\\.${sectionName}\\.(\\w*)$`)
      );
      if (sectionMatch) {
        const typed = sectionMatch[1];
        const componentOptions = section.components.map((comp) => {
          const fieldName = toSnakeCase(comp.field_name);
          return {
            label: fieldName,
            type: "property",
            info: `${comp.component_type}: ${comp.label}`,
            detail: comp.component_type
          };
        });
        return {
          from: context.pos - typed.length,
          options: componentOptions,
          validFor: /^\w*$/
        };
      }
    }
    const settingsMatch = beforeCursor.match(/self\.settings_schema\.(\w*)$/);
    if (settingsMatch) {
      const typed = settingsMatch[1];
      const sectionOptions = sections.map((section) => {
        const sectionName = section.name || toSnakeCase(section.title || "section");
        const sectionTitle = section.title || section.name || "Section";
        return {
          label: sectionName,
          type: "property",
          info: `Section: ${sectionTitle}`,
          detail: "Section"
        };
      });
      return {
        from: context.pos - typed.length,
        options: sectionOptions,
        validFor: /^\w*$/
      };
    }
    const selfDotMatch = beforeCursor.match(/self\.(\w*)$/);
    if (selfDotMatch) {
      const typed = selfDotMatch[1];
      return {
        from: context.pos - typed.length,
        options: [{ label: "settings_schema", type: "property", info: "Access node settings" }],
        validFor: /^\w*$/
      };
    }
    const lfMethodMatch = beforeCursor.match(/(\w+)\.(\w*)$/);
    if (lfMethodMatch) {
      const typed = lfMethodMatch[2];
      return {
        from: context.pos - typed.length,
        options: lazyFrameMethods,
        validFor: /^\w*$/
      };
    }
    const wordMatch = context.matchBefore(/\w+/);
    if (!wordMatch && !context.explicit) return null;
    return {
      from: wordMatch ? wordMatch.from : context.pos,
      options: polarsCompletions,
      validFor: /^\w*$/
    };
  }
  const tabKeymap = keymap.of([
    {
      key: "Tab",
      run: (view) => {
        if (acceptCompletion(view)) {
          return true;
        }
        return indentMore(view);
      }
    },
    {
      key: "Shift-Tab",
      run: (view) => {
        return indentLess(view);
      }
    }
  ]);
  const extensions = [
    python(),
    oneDark,
    EditorState.tabSize.of(4),
    autocompletion({
      override: [schemaCompletions],
      defaultKeymap: true,
      // Enable default keymap for arrow navigation
      closeOnBlur: false
    }),
    Prec.highest(tabKeymap)
    // Tab keymap with highest precedence
  ];
  const readOnlyExtensions = [
    python(),
    oneDark,
    EditorState.tabSize.of(4),
    EditorView.editable.of(false),
    EditorState.readOnly.of(true)
  ];
  return {
    extensions,
    readOnlyExtensions,
    schemaCompletions
  };
}
const _hoisted_1 = { class: "node-designer-container" };
const _hoisted_2 = { class: "page-header" };
const _hoisted_3 = { class: "header-actions" };
const _hoisted_4 = { class: "designer-layout" };
const _hoisted_5 = { class: "panel design-canvas" };
const _hoisted_6 = { class: "panel-content" };
const _hoisted_7 = { class: "metadata-section" };
const _hoisted_8 = { class: "form-grid" };
const _hoisted_9 = { class: "form-field" };
const _hoisted_10 = { class: "form-field" };
const _hoisted_11 = { class: "form-field" };
const _hoisted_12 = { class: "form-field" };
const _hoisted_13 = { class: "form-field" };
const _hoisted_14 = { class: "form-field" };
const _hoisted_15 = { class: "form-field icon-field" };
const _hoisted_16 = { class: "sections-area" };
const _hoisted_17 = { class: "sections-header" };
const _hoisted_18 = {
  key: 0,
  class: "empty-sections"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "NodeDesigner",
  setup(__props) {
    const {
      nodeMetadata,
      sections,
      selectedSectionIndex,
      selectedComponentIndex,
      processCode,
      selectedComponent,
      addSection,
      removeSection,
      selectSection,
      sanitizeSectionName,
      selectComponent,
      removeComponent,
      addComponentToSection,
      resetState,
      getState,
      setState
    } = useNodeDesignerState();
    const validation = useNodeValidation();
    const codeGen = useCodeGeneration();
    const nodeBrowser = useNodeBrowser();
    const autocompletion2 = usePolarsAutocompletion(() => sections.value);
    const storage = useSessionStorage(getState, setState, resetState);
    const showHelpModal = ref(false);
    watch([() => ({ ...nodeMetadata }), sections, processCode], () => storage.saveToSessionStorage(), {
      deep: true
    });
    onMounted(() => {
      storage.loadFromSessionStorage();
    });
    function handleNew() {
      storage.clearSessionStorage();
    }
    function handlePreview() {
      codeGen.previewCode(nodeMetadata, sections.value, processCode.value);
    }
    async function handleSave() {
      var _a, _b;
      const errors = validation.validateSettings(nodeMetadata, sections.value, processCode.value);
      if (errors.length > 0) {
        validation.showErrors(errors);
        return;
      }
      const code = codeGen.generateCode(nodeMetadata, sections.value, processCode.value);
      const fileName = toSnakeCase(nodeMetadata.node_name) + ".py";
      try {
        await axios.post("/user_defined_components/save-custom-node", {
          file_name: fileName,
          code
        });
        alert(`Node "${nodeMetadata.node_name}" saved successfully!`);
      } catch (error) {
        const errorMsg = ((_b = (_a = error.response) == null ? void 0 : _a.data) == null ? void 0 : _b.detail) || error.message || "Failed to save node";
        alert(`Error saving node: ${errorMsg}`);
      }
    }
    function handleDrop(event, sectionIndex) {
      var _a;
      const componentType = (_a = event.dataTransfer) == null ? void 0 : _a.getData("component_type");
      if (!componentType) return;
      const compCount = sections.value[sectionIndex].components.length + 1;
      const newComponent = {
        component_type: componentType,
        field_name: `${toSnakeCase(componentType)}_${compCount}`,
        label: `${componentType} ${compCount}`,
        options_source: "static",
        options_string: ""
      };
      if (componentType === "TextInput") {
        newComponent.default = "";
        newComponent.placeholder = "";
      } else if (componentType === "NumericInput") {
        newComponent.default = 0;
      } else if (componentType === "ToggleSwitch") {
        newComponent.default = false;
      } else if (componentType === "ColumnSelector") {
        newComponent.required = false;
        newComponent.multiple = false;
        newComponent.data_types = "ALL";
      } else if (componentType === "ColumnActionInput") {
        newComponent.actions_string = "sum, mean, min, max";
        newComponent.output_name_template = "{column}_{action}";
        newComponent.show_group_by = false;
        newComponent.show_order_by = false;
        newComponent.data_types = "ALL";
      } else if (componentType === "SliderInput") {
        newComponent.min_value = 0;
        newComponent.max_value = 100;
        newComponent.step = 1;
      }
      addComponentToSection(sectionIndex, newComponent);
    }
    function handlePropertyUpdate(field, value) {
      if (selectedComponent.value) {
        selectedComponent.value[field] = value;
      }
    }
    const selectedSectionName = computed(() => {
      if (selectedSectionIndex.value === null) return "";
      const section = sections.value[selectedSectionIndex.value];
      return (section == null ? void 0 : section.name) || (section == null ? void 0 : section.title) || "";
    });
    function handleInsertVariable(code) {
      const lines = processCode.value.split("\n");
      let insertIndex = 1;
      for (let i = 0; i < lines.length; i++) {
        const trimmed = lines[i].trim();
        if (trimmed.startsWith("def process")) {
          insertIndex = i + 1;
          while (insertIndex < lines.length && (lines[insertIndex].trim().startsWith("#") || lines[insertIndex].trim() === "")) {
            insertIndex++;
          }
          break;
        }
      }
      lines.splice(insertIndex, 0, code);
      processCode.value = lines.join("\n");
    }
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          _cache[25] || (_cache[25] = createBaseVNode("div", { class: "header-left" }, [
            createBaseVNode("h2", { class: "page-title" }, "Node Designer"),
            createBaseVNode("p", { class: "page-description" }, "Design custom nodes visually")
          ], -1)),
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("button", {
              class: "btn btn-secondary",
              onClick: _cache[0] || (_cache[0] = ($event) => showHelpModal.value = true)
            }, [..._cache[20] || (_cache[20] = [
              createBaseVNode("i", { class: "fa-solid fa-circle-question" }, null, -1),
              createTextVNode(" Help ", -1)
            ])]),
            createBaseVNode("button", {
              class: "btn btn-secondary",
              onClick: _cache[1] || (_cache[1] = ($event) => unref(nodeBrowser).openNodeBrowser())
            }, [..._cache[21] || (_cache[21] = [
              createBaseVNode("i", { class: "fa-solid fa-folder-open" }, null, -1),
              createTextVNode(" Browse ", -1)
            ])]),
            createBaseVNode("button", {
              class: "btn btn-secondary",
              onClick: handleNew
            }, [..._cache[22] || (_cache[22] = [
              createBaseVNode("i", { class: "fa-solid fa-file" }, null, -1),
              createTextVNode(" New ", -1)
            ])]),
            createBaseVNode("button", {
              class: "btn btn-secondary",
              onClick: handlePreview
            }, [..._cache[23] || (_cache[23] = [
              createBaseVNode("i", { class: "fa-solid fa-code" }, null, -1),
              createTextVNode(" Preview ", -1)
            ])]),
            createBaseVNode("button", {
              class: "btn btn-primary",
              onClick: handleSave
            }, [..._cache[24] || (_cache[24] = [
              createBaseVNode("i", { class: "fa-solid fa-save" }, null, -1),
              createTextVNode(" Save ", -1)
            ])])
          ])
        ]),
        createBaseVNode("div", _hoisted_4, [
          createVNode(ComponentPalette),
          createBaseVNode("div", _hoisted_5, [
            _cache[36] || (_cache[36] = createBaseVNode("div", { class: "panel-header" }, [
              createBaseVNode("h3", null, "Design Canvas")
            ], -1)),
            createBaseVNode("div", _hoisted_6, [
              createBaseVNode("div", _hoisted_7, [
                _cache[32] || (_cache[32] = createBaseVNode("h4", null, "Node Metadata", -1)),
                createBaseVNode("div", _hoisted_8, [
                  createBaseVNode("div", _hoisted_9, [
                    _cache[26] || (_cache[26] = createBaseVNode("label", { for: "node-name" }, "Node Name *", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "node-name",
                      "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => unref(nodeMetadata).node_name = $event),
                      type: "text",
                      class: "form-input",
                      placeholder: "My Custom Node"
                    }, null, 512), [
                      [vModelText, unref(nodeMetadata).node_name]
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_10, [
                    _cache[27] || (_cache[27] = createBaseVNode("label", { for: "node-category" }, "Category *", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "node-category",
                      "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => unref(nodeMetadata).node_category = $event),
                      type: "text",
                      class: "form-input",
                      placeholder: "Custom"
                    }, null, 512), [
                      [vModelText, unref(nodeMetadata).node_category]
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_11, [
                    _cache[28] || (_cache[28] = createBaseVNode("label", { for: "node-title" }, "Title", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "node-title",
                      "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => unref(nodeMetadata).title = $event),
                      type: "text",
                      class: "form-input",
                      placeholder: "My Custom Node"
                    }, null, 512), [
                      [vModelText, unref(nodeMetadata).title]
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_12, [
                    _cache[29] || (_cache[29] = createBaseVNode("label", { for: "node-intro" }, "Description", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "node-intro",
                      "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => unref(nodeMetadata).intro = $event),
                      type: "text",
                      class: "form-input",
                      placeholder: "A custom node for data processing"
                    }, null, 512), [
                      [vModelText, unref(nodeMetadata).intro]
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_13, [
                    _cache[30] || (_cache[30] = createBaseVNode("label", { for: "node-inputs" }, "Number of Inputs", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "node-inputs",
                      "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => unref(nodeMetadata).number_of_inputs = $event),
                      type: "number",
                      min: "0",
                      max: "10",
                      class: "form-input"
                    }, null, 512), [
                      [
                        vModelText,
                        unref(nodeMetadata).number_of_inputs,
                        void 0,
                        { number: true }
                      ]
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_14, [
                    _cache[31] || (_cache[31] = createBaseVNode("label", { for: "node-outputs" }, "Number of Outputs", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "node-outputs",
                      "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => unref(nodeMetadata).number_of_outputs = $event),
                      type: "number",
                      min: "1",
                      max: "10",
                      class: "form-input"
                    }, null, 512), [
                      [
                        vModelText,
                        unref(nodeMetadata).number_of_outputs,
                        void 0,
                        { number: true }
                      ]
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_15, [
                    createVNode(IconSelector, {
                      modelValue: unref(nodeMetadata).node_icon,
                      "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => unref(nodeMetadata).node_icon = $event)
                    }, null, 8, ["modelValue"])
                  ])
                ])
              ]),
              createBaseVNode("div", _hoisted_16, [
                createBaseVNode("div", _hoisted_17, [
                  _cache[34] || (_cache[34] = createBaseVNode("h4", null, "UI Sections", -1)),
                  createBaseVNode("button", {
                    class: "add-section-btn",
                    onClick: _cache[9] || (_cache[9] = ($event) => unref(addSection)())
                  }, [..._cache[33] || (_cache[33] = [
                    createBaseVNode("i", { class: "fa-solid fa-plus" }, null, -1),
                    createTextVNode(" Add Section ", -1)
                  ])])
                ]),
                (openBlock(true), createElementBlock(Fragment, null, renderList(unref(sections), (section, sectionIndex) => {
                  return openBlock(), createBlock(SectionCard, {
                    key: sectionIndex,
                    section,
                    "is-selected": unref(selectedSectionIndex) === sectionIndex,
                    "selected-component-index": unref(selectedSectionIndex) === sectionIndex ? unref(selectedComponentIndex) : null,
                    onSelect: ($event) => unref(selectSection)(sectionIndex),
                    onRemove: ($event) => unref(removeSection)(sectionIndex),
                    onSelectComponent: ($event) => unref(selectComponent)(sectionIndex, $event),
                    onRemoveComponent: ($event) => unref(removeComponent)(sectionIndex, $event),
                    onDrop: ($event) => handleDrop($event, sectionIndex),
                    onUpdateName: ($event) => {
                      section.name = $event;
                      unref(sanitizeSectionName)(sectionIndex);
                    },
                    onUpdateTitle: ($event) => section.title = $event
                  }, null, 8, ["section", "is-selected", "selected-component-index", "onSelect", "onRemove", "onSelectComponent", "onRemoveComponent", "onDrop", "onUpdateName", "onUpdateTitle"]);
                }), 128)),
                unref(sections).length === 0 ? (openBlock(), createElementBlock("div", _hoisted_18, [..._cache[35] || (_cache[35] = [
                  createBaseVNode("i", { class: "fa-solid fa-layer-group" }, null, -1),
                  createBaseVNode("p", null, "No sections yet. Add a section to start designing your node UI.", -1)
                ])])) : createCommentVNode("", true)
              ]),
              createVNode(ProcessCodeEditor, {
                modelValue: unref(processCode),
                "onUpdate:modelValue": _cache[10] || (_cache[10] = ($event) => isRef(processCode) ? processCode.value = $event : null),
                extensions: unref(autocompletion2).extensions
              }, null, 8, ["modelValue", "extensions"])
            ])
          ]),
          createVNode(PropertyEditor, {
            component: unref(selectedComponent),
            "section-name": selectedSectionName.value,
            onUpdate: handlePropertyUpdate,
            onInsertVariable: handleInsertVariable
          }, null, 8, ["component", "section-name"])
        ]),
        createVNode(CodePreviewModal, {
          show: unref(codeGen).showPreviewModal.value,
          code: unref(codeGen).generatedCode.value,
          onClose: _cache[11] || (_cache[11] = ($event) => unref(codeGen).closePreview())
        }, null, 8, ["show", "code"]),
        createVNode(ValidationModal, {
          show: unref(validation).showValidationModal.value,
          errors: unref(validation).validationErrors.value,
          onClose: _cache[12] || (_cache[12] = ($event) => unref(validation).closeValidationModal())
        }, null, 8, ["show", "errors"]),
        createVNode(NodeBrowserModal, {
          show: unref(nodeBrowser).showNodeBrowser.value,
          nodes: unref(nodeBrowser).customNodes.value,
          loading: unref(nodeBrowser).loadingNodes.value,
          "viewing-node-code": unref(nodeBrowser).viewingNodeCode.value,
          "viewing-node-name": unref(nodeBrowser).viewingNodeName.value,
          "show-delete-confirm": unref(nodeBrowser).showDeleteConfirm.value,
          "read-only-extensions": unref(autocompletion2).readOnlyExtensions,
          onClose: _cache[13] || (_cache[13] = ($event) => unref(nodeBrowser).closeNodeBrowser()),
          onViewNode: _cache[14] || (_cache[14] = ($event) => unref(nodeBrowser).viewCustomNode($event)),
          onBack: _cache[15] || (_cache[15] = ($event) => unref(nodeBrowser).backToNodeList()),
          onConfirmDelete: _cache[16] || (_cache[16] = ($event) => unref(nodeBrowser).confirmDeleteNode()),
          onCancelDelete: _cache[17] || (_cache[17] = ($event) => unref(nodeBrowser).showDeleteConfirm.value = false),
          onDelete: _cache[18] || (_cache[18] = ($event) => unref(nodeBrowser).deleteNode())
        }, null, 8, ["show", "nodes", "loading", "viewing-node-code", "viewing-node-name", "show-delete-confirm", "read-only-extensions"]),
        createVNode(NodeDesignerHelpModal, {
          show: showHelpModal.value,
          onClose: _cache[19] || (_cache[19] = ($event) => showHelpModal.value = false)
        }, null, 8, ["show"])
      ]);
    };
  }
});
const NodeDesigner = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-3db2802e"]]);
export {
  NodeDesigner as default
};
