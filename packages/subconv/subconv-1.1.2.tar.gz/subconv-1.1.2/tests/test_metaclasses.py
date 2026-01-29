from subconv._metaclasses import SingletonMeta


class TestSingletonMeta:
    def setup_method(self):
        SingletonMeta._instances.clear()

    def teardown_method(self):
        SingletonMeta._instances.clear()

    def test_same_instance_returned(self):
        class MySingleton(metaclass=SingletonMeta):
            def __init__(self, value):
                self.value = value

        instance1 = MySingleton(1)
        instance2 = MySingleton(2)

        assert instance1 is instance2

    def test_first_init_args_used(self):
        class MySingleton(metaclass=SingletonMeta):
            def __init__(self, value):
                self.value = value

        instance1 = MySingleton(1)
        instance2 = MySingleton(2)

        assert instance1.value == 1
        assert instance2.value == 1

    def test_different_classes_have_different_instances(self):
        class Singleton1(metaclass=SingletonMeta):
            pass

        class Singleton2(metaclass=SingletonMeta):
            pass

        instance1 = Singleton1()
        instance2 = Singleton2()

        assert instance1 is not instance2

    def test_subclasses_have_separate_instances(self):
        class Parent(metaclass=SingletonMeta):
            pass

        class Child(Parent):
            pass

        parent = Parent()
        child = Child()

        assert parent is not child

    def test_kwargs_in_init(self):
        class MySingleton(metaclass=SingletonMeta):
            def __init__(self, *, name="default"):
                self.name = name

        instance1 = MySingleton(name="first")
        instance2 = MySingleton(name="second")

        assert instance1.name == "first"
        assert instance2.name == "first"

    def test_instances_persist(self):
        class MySingleton(metaclass=SingletonMeta):
            counter = 0

            def __init__(self):
                MySingleton.counter += 1

        MySingleton()
        MySingleton()
        MySingleton()

        assert MySingleton.counter == 1

    def test_no_args_singleton(self):
        class SimpleSingleton(metaclass=SingletonMeta):
            pass

        instance1 = SimpleSingleton()
        instance2 = SimpleSingleton()

        assert instance1 is instance2

    def test_complex_args(self):
        class MySingleton(metaclass=SingletonMeta):
            def __init__(self, items, config=None):
                self.items = items
                self.config = config

        instance = MySingleton([1, 2, 3], config={"key": "value"})

        assert instance.items == [1, 2, 3]
        assert instance.config == {"key": "value"}
