Java.perform(function () {
  const classNames = [
    "com.meicai.mall.xy",
    "com.meicai.mall.CategoryViewModel",
    "com.meicai.mall.category.CategoryViewModel$a",
    "com.meicai.mall.category.CategoryViewModel$b",
    "com.meicai.mall.category.CategoryViewModel$c",
    "com.meicai.mall.category.CategoryViewModel$d",
    "com.meicai.mall.category.CategoryViewModel$e",
    "com.meicai.mall.category.CategoryViewModel$f",
    "com.meicai.mall.category.CategoryViewModel$g",
    "com.meicai.mall.category.CategoryViewModel$h",
    "com.meicai.mall.domain.Category",
    "com.meicai.mall.net.result.CategoryResult",
    "com.meicai.mall.net.result.SearchBiAndBrandBean",
    "com.meicai.mall.net.params.Label",
    "com.meicai.mall.bean.HorizontalScrollTitleBean",
  ];

  function emit(payload) {
    send({
      type: "meicai_target_inspector",
      payload: payload,
    });
  }

  function describeAnnotations(reflectiveObject) {
    const annotations = reflectiveObject.getDeclaredAnnotations();
    const values = [];
    for (let index = 0; index < annotations.length; index += 1) {
      values.push(String(annotations[index].toString()));
    }
    return values;
  }

  function describeClass(className) {
    try {
      const javaClass = Java.use(className).class;
      const fields = javaClass.getDeclaredFields();
      const constructors = javaClass.getDeclaredConstructors();
      const methods = javaClass.getDeclaredMethods();
      const fieldItems = [];
      const constructorItems = [];
      const methodItems = [];
      for (let index = 0; index < fields.length; index += 1) {
        fieldItems.push(String(fields[index].toString()));
      }
      for (let index = 0; index < constructors.length; index += 1) {
        constructorItems.push(String(constructors[index].toString()));
      }
      for (let index = 0; index < methods.length; index += 1) {
        methodItems.push({
          signature: String(methods[index].toString()),
          annotations: describeAnnotations(methods[index]),
        });
      }
      emit({
        className: className,
        loader: String(javaClass.getClassLoader()),
        superclass: String(javaClass.getSuperclass()),
        interfaces: String(javaClass.getInterfaces()),
        fields: fieldItems,
        constructors: constructorItems,
        methods: methodItems,
      });
    } catch (error) {
      emit({
        className: className,
        error: String(error),
      });
    }
  }

  classNames.forEach(describeClass);
});
