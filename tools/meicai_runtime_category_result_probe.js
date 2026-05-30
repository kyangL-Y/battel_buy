Java.perform(function () {
  const seenIds = {};
  let eventCount = 0;

  function emit(payload) {
    send({
      type: "meicai_category_result_probe",
      payload: payload,
    });
  }

  function safeJson(javaObject) {
    try {
      const Gson = Java.use("com.google.gson.Gson");
      return String(Gson.$new().toJson(javaObject));
    } catch (error) {
      return "";
    }
  }

  function parseJson(text) {
    try {
      return JSON.parse(text);
    } catch (error) {
      return null;
    }
  }

  function topKeys(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      return [];
    }
    return Object.keys(value).sort();
  }

  function arrayAtPath(value, path) {
    let current = value;
    for (let index = 0; index < path.length; index += 1) {
      if (!current || typeof current !== "object") {
        return null;
      }
      current = current[path[index]];
    }
    return Array.isArray(current) ? current : null;
  }

  function findRows(value) {
    const paths = [
      ["rows"],
      ["list"],
      ["goodsRows"],
      ["data", "rows"],
      ["data", "list"],
      ["pageData", "rows"],
      ["pageData", "list"],
    ];
    for (let index = 0; index < paths.length; index += 1) {
      const rows = arrayAtPath(value, paths[index]);
      if (rows) {
        return {
          path: paths[index].join("."),
          rows: rows,
        };
      }
    }
    return {
      path: "",
      rows: [],
    };
  }

  function goodsIdentity(row) {
    if (!row || typeof row !== "object") {
      return "";
    }
    const skuBase = row.skuBase && typeof row.skuBase === "object" ? row.skuBase : {};
    return String(skuBase.skuId || skuBase.spuId || row.skuId || row.spuId || "");
  }

  function summarizeRows(rows) {
    let newUniqueCount = 0;
    const fieldKeys = {};
    rows.slice(0, 5).forEach(function (row) {
      if (!row || typeof row !== "object") {
        return;
      }
      Object.keys(row).forEach(function (key) {
        fieldKeys[key] = true;
      });
    });
    rows.forEach(function (row) {
      const id = goodsIdentity(row);
      if (id && !seenIds[id]) {
        seenIds[id] = true;
        newUniqueCount += 1;
      }
    });
    return {
      row_count: rows.length,
      new_unique_count: newUniqueCount,
      total_unique_count: Object.keys(seenIds).length,
      row_field_keys: Object.keys(fieldKeys).sort(),
    };
  }

  try {
    const CategoryViewModel = Java.use("com.meicai.mall.category.CategoryViewModel");
    CategoryViewModel.c.overload(
      "com.meicai.mall.net.result.BaseResult",
      "java.lang.String",
      "java.lang.String"
    ).implementation = function (baseResult, class1Id, class2Id) {
      const parsedResult = this.c(baseResult, class1Id, class2Id);
      eventCount += 1;
      const text = safeJson(parsedResult);
      const parsedJson = parseJson(text);
      const rowsInfo = findRows(parsedJson);
      const rowSummary = summarizeRows(rowsInfo.rows);
      emit({
        event_count: eventCount,
        class1_id: String(class1Id || ""),
        class2_id: String(class2Id || ""),
        json_length: text.length,
        top_keys: topKeys(parsedJson),
        row_path: rowsInfo.path,
        row_count: rowSummary.row_count,
        new_unique_count: rowSummary.new_unique_count,
        total_unique_count: rowSummary.total_unique_count,
        row_field_keys: rowSummary.row_field_keys,
      });
      return parsedResult;
    };
    emit({ status: "hooked", method: "CategoryViewModel.c(BaseResult,String,String)" });
  } catch (error) {
    emit({ status: "hook_error", error: String(error) });
  }
});
