Java.perform(function () {
  const ownerPattern = /^com\.meicai\./;
  const hitPattern = /(getSpusByClass|spus|saleClass|xbFeed|goodsInfoLocation|smartList|getGoodList|dishes|recommend|Search|search|IQuick|Quick|MallSearch|keyword|getData|getEncryption|saltMessage|encryption|convert|responseCheck|CategoryViewModel|AllGoodsList|CategoryGoodsList|PurchasingService)/i;
  let scannedClassCount = 0;
  let hitClassCount = 0;

  function emit(payload) {
    send({
      type: "meicai_method_finder",
      payload: payload,
    });
  }

  function annotationsFor(method) {
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
      scannedClassCount += 1;
      try {
        const javaClass = Java.use(className).class;
        const fields = javaClass.getDeclaredFields();
        const methods = javaClass.getDeclaredMethods();
        const fieldHits = [];
        const methodHits = [];
        for (let index = 0; index < fields.length; index += 1) {
          const fieldText = String(fields[index].toString());
          if (hitPattern.test(fieldText)) {
            fieldHits.push(fieldText);
          }
        }
        for (let index = 0; index < methods.length; index += 1) {
          const methodText = String(methods[index].toString());
          const annotationItems = annotationsFor(methods[index]);
          const joinedText = methodText + " " + annotationItems.join(" ");
          if (hitPattern.test(joinedText)) {
            methodHits.push({
              signature: methodText,
              annotations: annotationItems,
            });
          }
        }
        if (fieldHits.length > 0 || methodHits.length > 0) {
          hitClassCount += 1;
          emit({
            className: className,
            loader: String(javaClass.getClassLoader()),
            fields: fieldHits.slice(0, 60),
            methods: methodHits.slice(0, 80),
          });
        }
      } catch (error) {
        if (hitPattern.test(className)) {
          emit({
            className: className,
            error: String(error),
          });
        }
      }
    },
    onComplete: function () {
      emit({
        status: "complete",
        scannedClassCount: scannedClassCount,
        hitClassCount: hitClassCount,
      });
    },
  });
});
