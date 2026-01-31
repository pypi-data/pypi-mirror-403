const createSelectInputFromName = (columnName, keep = true) => {
  return {
    old_name: columnName,
    new_name: columnName,
    keep,
    is_altered: false,
    data_type_change: false,
    is_available: true,
    position: 0,
    original_position: 0
  };
};
function isInputCsvTable(settings) {
  return settings.file_type === "csv";
}
function isInputExcelTable(settings) {
  return settings.file_type === "excel";
}
function isInputParquetTable(settings) {
  return settings.file_type === "parquet";
}
function isOutputCsvTable(settings) {
  return settings.file_type === "csv";
}
function isOutputParquetTable(settings) {
  return settings.file_type === "parquet";
}
function isOutputExcelTable(settings) {
  return settings.file_type === "excel";
}
const FILTER_OPERATOR_LABELS = {
  Equals: "equals",
  "Does not equal": "not_equals",
  "Greater than": "greater_than",
  "Greater than or equals": "greater_than_or_equals",
  "Less than": "less_than",
  "Less than or equals": "less_than_or_equals",
  Contains: "contains",
  "Does not contain": "not_contains",
  "Starts with": "starts_with",
  "Ends with": "ends_with",
  "Is null": "is_null",
  "Is not null": "is_not_null",
  In: "in",
  "Not in": "not_in",
  Between: "between"
};
const FILTER_OPERATOR_REVERSE_LABELS = {
  equals: "Equals",
  not_equals: "Does not equal",
  greater_than: "Greater than",
  greater_than_or_equals: "Greater than or equals",
  less_than: "Less than",
  less_than_or_equals: "Less than or equals",
  contains: "Contains",
  not_contains: "Does not contain",
  starts_with: "Starts with",
  ends_with: "Ends with",
  is_null: "Is null",
  is_not_null: "Is not null",
  in: "In",
  not_in: "Not in",
  between: "Between"
};
function getFilterOperatorLabel(operator) {
  return FILTER_OPERATOR_REVERSE_LABELS[operator] || operator;
}
const OPERATORS_WITH_VALUE2 = ["between"];
const OPERATORS_NO_VALUE = ["is_null", "is_not_null"];
export {
  FILTER_OPERATOR_LABELS as F,
  OPERATORS_WITH_VALUE2 as O,
  OPERATORS_NO_VALUE as a,
  isOutputExcelTable as b,
  isOutputParquetTable as c,
  isInputExcelTable as d,
  isInputCsvTable as e,
  isInputParquetTable as f,
  getFilterOperatorLabel as g,
  createSelectInputFromName as h,
  isOutputCsvTable as i
};
