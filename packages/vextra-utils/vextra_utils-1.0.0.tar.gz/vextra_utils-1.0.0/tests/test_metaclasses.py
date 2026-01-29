from threading import Thread

from vextra_utils import SingletonMeta


class TestSingletonMeta:
    def setup_method(self) -> None:
        SingletonMeta.clear_instances()

    def teardown_method(self) -> None:
        SingletonMeta.clear_instances()

    def test_returns_same_instance(self) -> None:
        class Database(metaclass=SingletonMeta):
            def __init__(self) -> None:
                self.connection = "connected"

        db1 = Database()
        db2 = Database()

        assert db1 is db2

    def test_init_called_once(self) -> None:
        call_count = 0

        class Counter(metaclass=SingletonMeta):
            def __init__(self) -> None:
                nonlocal call_count
                call_count += 1

        Counter()
        Counter()
        Counter()

        assert call_count == 1

    def test_preserves_init_arguments(self) -> None:
        class Config(metaclass=SingletonMeta):
            def __init__(self, value: str) -> None:
                self.value = value

        config1 = Config("first")
        config2 = Config("second")

        assert config1.value == "first"
        assert config2.value == "first"
        assert config1 is config2

    def test_different_classes_have_different_instances(self) -> None:
        class ServiceA(metaclass=SingletonMeta):
            pass

        class ServiceB(metaclass=SingletonMeta):
            pass

        a1 = ServiceA()
        a2 = ServiceA()
        b1 = ServiceB()
        b2 = ServiceB()

        assert a1 is a2
        assert b1 is b2
        assert a1 is not b1

    def test_clear_instances_removes_all_singletons(self) -> None:
        class Service(metaclass=SingletonMeta):
            def __init__(self) -> None:
                self.id = id(self)

        s1 = Service()
        first_id = s1.id

        SingletonMeta.clear_instances()

        s2 = Service()
        second_id = s2.id

        assert first_id != second_id
        assert s1 is not s2

    def test_thread_safety(self) -> None:
        instances: list[object] = []

        class ThreadSafeService(metaclass=SingletonMeta):
            def __init__(self) -> None:
                self.value = "initialized"

        def create_instance() -> None:
            instance = ThreadSafeService()
            instances.append(instance)

        threads = [Thread(target=create_instance) for _ in range(100)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(instances) == 100
        assert all(inst is instances[0] for inst in instances)

    def test_inheritance(self) -> None:
        class BaseService(metaclass=SingletonMeta):
            def __init__(self) -> None:
                self.name = "base"

        class DerivedService(BaseService):
            def __init__(self) -> None:
                super().__init__()
                self.name = "derived"

        base1 = BaseService()
        base2 = BaseService()
        derived1 = DerivedService()
        derived2 = DerivedService()

        assert base1 is base2
        assert derived1 is derived2
        assert base1 is not derived1
        assert base1.name == "base"
        assert derived1.name == "derived"

    def test_instance_attributes_persist(self) -> None:
        class StatefulService(metaclass=SingletonMeta):
            def __init__(self) -> None:
                self.data: list[int] = []

        service1 = StatefulService()
        service1.data.append(1)
        service1.data.append(2)

        service2 = StatefulService()

        assert service2.data == [1, 2]
        assert service1.data is service2.data
