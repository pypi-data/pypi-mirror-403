# coding: utf-8

def singleton_decorator(_class):
    """
    Using:
    @singleton_decorator
    class MyClass(BaseClass):
        ...

    ``` Python
    @ksupk_singleton_decorator
    class ClassA:

        def __init__(self, kek):
            self._var1 = kek
            self._var2 = gen_random_string()

        def info(self):
            print(self._var1)
            print(self._var2)

    a = ClassA(5)
    b = ClassA(7)

    a.info()  # will print: 5 and kxRUr9wEhphsp4HpsF19
    b.info()  # will print: 5 and kxRUr9wEhphsp4HpsF19
    print(a == b)  # will print: True
    ```

    Problem:
    While objects created using MyClass() would be true singleton objects, 
    MyClass itself is a function, not a class, so you cannot call class methods from it.
    """
    instances = {}
    def getinstance(*args, **kwargs):
        if _class not in instances:
            instances[_class] = _class(*args, **kwargs)
        return instances[_class]
    return getinstance
