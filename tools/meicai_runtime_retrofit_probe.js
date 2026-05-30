Java.perform(function () {
  const pathPattern = /(getSpusByClass|saleClass|xbFeed|goodsInfoLocation|smartList|getGoodList|\/entrance\/dishes|\/entrance\/recommend|\/entrance\/smartList|search|Search|quick|Quick|category|goodList|GoodsList)/i;
  const ownerPattern = /^com\.meicai\./;

  function emit(payload) {
    send({
      type: "meicai_retrofit_probe",
      payload: payload,
    });
  }

  function annotationTextList(method) {
    const annotations = method.getDeclaredAnnotations();
    const values = [];
    for (let index = 0; index < annotations.length; index += 1) {
      values.push(String(annotations[index].toString()));
    }
    return values;
  }

  Java.enumerateLoadedClasses({
    onMatch: function (className) {
      if (!ownerPattern.test(className)) {
        return;
      }
      try {
        const targetClass = Java.use(className).class;
        const methods = targetClass.getDeclaredMethods();
        const hits = [];
        for (let index = 0; index < methods.length; index += 1) {
          const annotations = annotationTextList(methods[index]);
          const annotationText = annotations.join(" ");
          if (!pathPattern.test(annotationText) && !pathPattern.test(String(methods[index].toString()))) {
            continue;
          }
          hits.push({
            signature: String(methods[index].toString()),
            annotations: annotations,
          });
        }
        if (hits.length > 0) {
          emit({
            className: className,
            loader: String(targetClass.getClassLoader()),
            methods: hits,
          });
        }
      } catch (error) {
        // Some generated or hidden classes reject reflection; keep the probe read-only and continue.
      }
    },
    onComplete: function () {
      emit({ status: "complete" });
    },
  });
});
