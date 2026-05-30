Java.perform(function () {
  const DexFile = Java.use("dalvik.system.DexFile");
  const ClassLoader = Java.use("java.lang.ClassLoader");
  const loaderLines = [];
  const dexLines = [];
  const classHits = [];
  const keywords = [
    "getSpusByClass",
    "saleClass",
    "xbFeed",
    "Encryption",
    "encryption",
    "Dishes",
    "Search",
    "Spu",
    "Sku",
    "Response",
  ];

  Java.enumerateClassLoaders({
    onMatch: function (loader) {
      loaderLines.push(loader.toString());
    },
    onComplete: function () {},
  });

  Java.enumerateLoadedClasses({
    onMatch: function (className) {
      for (let index = 0; index < keywords.length; index += 1) {
        if (className.indexOf(keywords[index]) >= 0) {
          classHits.push(className);
          break;
        }
      }
    },
    onComplete: function () {},
  });

  try {
    const Runtime = Java.use("java.lang.Runtime");
    const process = Runtime.getRuntime().exec(["sh", "-c", "cat /proc/self/maps | grep -E '\\\\.dex|base.apk|split|meicai|stub|tianyu' | head -n 300"]);
    const BufferedReader = Java.use("java.io.BufferedReader");
    const InputStreamReader = Java.use("java.io.InputStreamReader");
    const reader = BufferedReader.$new(InputStreamReader.$new(process.getInputStream()));
    let line = reader.readLine();
    while (line !== null) {
      dexLines.push(line);
      line = reader.readLine();
    }
  } catch (error) {
    dexLines.push("maps_error=" + error);
  }

  send({
    type: "meicai_runtime_probe",
    classLoaderCount: loaderLines.length,
    classLoaders: loaderLines.slice(0, 80),
    classHitCount: classHits.length,
    classHits: classHits.slice(0, 300),
    dexMaps: dexLines,
  });
});
