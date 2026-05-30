Java.perform(function () {
  const keywordPattern = /(meicai|shenfeifei|stub|tianyu|dishes|spus|sku|encrypt|decrypt|response|category)/i;
  const seenClassNames = {};

  function emit(eventType, payload) {
    send({
      type: eventType,
      payload: payload,
    });
  }

  function summarizeClassName(className) {
    const text = String(className || "");
    if (!keywordPattern.test(text)) {
      return;
    }
    if (seenClassNames[text]) {
      return;
    }
    seenClassNames[text] = true;
    emit("meicai_class_hit", { className: text });
  }

  function hookMethod(className, methodName, callback) {
    try {
      const targetClass = Java.use(className);
      const overloads = targetClass[methodName].overloads;
      overloads.forEach(function (overload) {
        overload.implementation = function () {
          callback(className, methodName, arguments);
          return overload.apply(this, arguments);
        };
      });
      emit("meicai_hooked_method", { className: className, methodName: methodName, overloads: overloads.length });
    } catch (error) {
      emit("meicai_hook_error", { className: className, methodName: methodName, error: String(error) });
    }
  }

  function summarizeLoaderArgs(className, methodName, args) {
    const values = [];
    for (let index = 0; index < args.length; index += 1) {
      values.push(String(args[index]));
    }
    emit("meicai_loader_call", { className: className, methodName: methodName, args: values.slice(0, 4) });
  }

  hookMethod("dalvik.system.BaseDexClassLoader", "$init", summarizeLoaderArgs);
  hookMethod("dalvik.system.DexClassLoader", "$init", summarizeLoaderArgs);

  try {
    hookMethod("dalvik.system.InMemoryDexClassLoader", "$init", function (className, methodName, args) {
      const values = [];
      for (let index = 0; index < args.length; index += 1) {
        const valueText = String(args[index]);
        values.push(valueText.length > 120 ? valueText.slice(0, 120) + "..." : valueText);
      }
      emit("meicai_loader_call", { className: className, methodName: methodName, args: values });
    });
  } catch (error) {
    emit("meicai_hook_error", { className: "dalvik.system.InMemoryDexClassLoader", methodName: "$init", error: String(error) });
  }

  hookMethod("java.lang.ClassLoader", "loadClass", function (_className, _methodName, args) {
    summarizeClassName(args[0]);
  });

  ["interface12", "interface14", "interface20", "interface21"].forEach(function (methodName) {
    hookMethod("com.stub.StubApp", methodName, function (className, currentMethodName, args) {
      const values = [];
      for (let index = 0; index < args.length; index += 1) {
        values.push(String(args[index]));
      }
      emit("meicai_stub_call", { className: className, methodName: currentMethodName, args: values.slice(0, 3) });
    });
  });

  Java.enumerateLoadedClasses({
    onMatch: summarizeClassName,
    onComplete: function () {
      emit("meicai_loader_probe_ready", { seenClassCount: Object.keys(seenClassNames).length });
    },
  });
});
