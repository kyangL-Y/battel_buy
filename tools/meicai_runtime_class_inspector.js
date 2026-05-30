Java.perform(function () {
  const classNames = [
    "com.meicai.mall.net.result.BaseResult",
    "com.meicai.mall.net.result.BaseResult$EncryptionBean",
    "com.meicai.mall.net.result.AllGoodsListResult",
    "com.meicai.mall.net.result.CategoryGoodsListBaseBean",
    "com.meicai.mall.category.CategoryViewModel",
    "com.meicai.mall.category.CategoryFragment",
    "com.meicai.mall.net.PurchasingService",
    "com.meicai.mall.net.IQuickService",
    "com.meicai.mall.module.search.viewmodel.SearchViewModel",
    "com.meicai.mall.module.search.SearchActivity",
    "com.meicai.mall.router.PageSearch",
    "com.meicai.mall.net.result.SearchBiAndBrandBean",
    "com.meicai.mall.bean.SearchKeyWordResult",
    "com.meicai.networkmodule.converter.IResponseConverter",
    "com.meicai.networkmodule.converter.UserResponseConvert",
    "com.meicai.networkmodule.converter.MCTypeAdapter",
    "com.meicai.networkmodule.converter.GsonTypeFit",
    "com.meicai.networkmodule.NetworkGenerator",
    "com.meicai.networkmodule.MCNetManager",
    "com.meicai.networkmodule.request.RequestDispacher",
  ];

  function emit(payload) {
    send({
      type: "meicai_class_inspector",
      payload: payload,
    });
  }

  function summarizeJavaArray(javaArray, limit, stringifyItem) {
    const items = [];
    const count = Math.min(javaArray.length, limit);
    for (let index = 0; index < count; index += 1) {
      items.push(stringifyItem(javaArray[index]));
    }
    return {
      total: javaArray.length,
      items: items,
    };
  }

  classNames.forEach(function (className) {
    try {
      const targetClass = Java.use(className);
      const javaClass = targetClass.class;
      const fields = summarizeJavaArray(javaClass.getDeclaredFields(), 80, function (field) {
        return String(field.toString());
      });
      const methods = summarizeJavaArray(javaClass.getDeclaredMethods(), 120, function (method) {
        const annotations = summarizeJavaArray(method.getDeclaredAnnotations(), 20, function (annotation) {
          return String(annotation.toString());
        });
        return {
          signature: String(method.toString()),
          annotations: annotations.items,
        };
      });
      emit({
        className: className,
        loader: String(javaClass.getClassLoader()),
        fields: fields,
        methods: methods,
      });
    } catch (error) {
      emit({
        className: className,
        error: String(error),
      });
    }
  });
});
