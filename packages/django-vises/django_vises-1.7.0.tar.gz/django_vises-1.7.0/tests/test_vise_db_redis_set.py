from uuid import UUID, uuid4

import pytest

from django_vises.db.redis_set import RedisSetInt, RedisSetStr, RedisSetUUID

from .common import REDIS_URI


@pytest.fixture
def test_values_str():
    return ("apple", "banana", "cherry")


@pytest.fixture
def empty_set_str():
    return RedisSetStr(redis_uri=REDIS_URI)


@pytest.fixture
def default_set_str(test_values_str):
    return RedisSetStr(test_values_str, redis_uri=REDIS_URI)


class TestRedisSetStr:
    def test_initial_set_is_empty(self, empty_set_str):
        """测试一个新创建的集合是否为空。"""
        assert len(empty_set_str) == 0
        assert "test" not in empty_set_str

    def test_add_and_membership(self, empty_set_str):
        """测试添加字符串元素和成员资格。"""
        empty_set_str.add("hello")
        empty_set_str.add("world")
        assert len(empty_set_str) == 2
        assert "hello" in empty_set_str
        assert "python" not in empty_set_str

    def test_add_duplicate_string(self, default_set_str):
        """测试添加重复字符串，长度不应改变。"""
        initial_len = len(default_set_str)
        default_set_str.add("apple")
        assert len(default_set_str) == initial_len

    def test_add_empty_string(self, empty_set_str):
        """测试集合可以存储空字符串。"""
        empty_set_str.add("")
        assert len(empty_set_str) == 1
        assert "" in empty_set_str

    def test_discard_existing_element(self, default_set_str):
        """测试移除一个存在的字符串元素。"""
        default_set_str.discard("banana")
        assert len(default_set_str) == 2
        assert "banana" not in default_set_str

    def test_discard_non_existing_element(self, default_set_str):
        """测试移除一个不存在的元素，不应引发错误。"""
        initial_len = len(default_set_str)
        default_set_str.discard("grape")
        assert len(default_set_str) == initial_len

    def test_iteration_and_contents(self, default_set_str):
        """测试集合的迭代。"""
        expected = {"apple", "banana", "cherry"}
        actual = set(default_set_str)
        assert actual == expected

    def test_case_sensitivity(self, default_set_str):
        """测试字符串集合是大小写敏感的。"""
        # 'Apple' 和 'apple' 是两个不同的元素
        default_set_str.add("Apple")
        assert len(default_set_str) == 4
        assert "Apple" in default_set_str
        assert "apple" in default_set_str  # 保持不变

    def test_contains_case_sensitivity(self, default_set_str):
        """测试成员资格检查是大小写敏感的。"""
        # 集合中有 'apple'
        assert "apple" in default_set_str
        # 集合中没有 'APPLE'
        assert "APPLE" not in default_set_str

    def test_type_enforcement_on_add(self, empty_set_str):
        """测试尝试添加非字符串类型时是否引发 TypeError。"""
        # Pytest 的 pytest.raises 上下文管理器用于检查异常
        with pytest.raises(TypeError):
            empty_set_str.add(123)  # 整数

        with pytest.raises(TypeError):
            empty_set_str.add(True)  # 布尔值

        with pytest.raises(TypeError):
            empty_set_str.add(["list"])  # 列表

    def test_repr(self, default_set_str, test_values_str):
        """测试 __repr__ 方法。"""
        items = repr(default_set_str).split(", ")
        assert set(items) == set(test_values_str)

    def test_as_set(self, default_set_str, test_values_str):
        assert default_set_str == set(test_values_str)


@pytest.fixture
def test_values_int():
    return (10, 20, 30)


@pytest.fixture
def empty_set_int():
    return RedisSetInt(redis_uri=REDIS_URI)


@pytest.fixture
def default_set_int(test_values_int):
    return RedisSetInt(test_values_int, redis_uri=REDIS_URI)


class TestRedisSetInt:
    def test_initial_empty_set_is_empty(self, empty_set_int):
        """测试一个新创建的集合是否为空。"""
        assert len(empty_set_int) == 0
        assert 5 not in empty_set_int

    def test_add_element(self, empty_set_int):
        """测试添加一个元素。"""
        empty_set_int.add(1)
        assert len(empty_set_int) == 1
        assert 1 in empty_set_int

    def test_add_duplicate_element(self, default_set_int):
        """测试添加重复元素，长度不应改变。"""
        initial_len = len(default_set_int)
        default_set_int.add(20)  # 20 已经存在
        assert len(default_set_int) == initial_len
        assert 20 in default_set_int

    def test_discard_existing_element(self, default_set_int):
        """测试移除一个存在的元素。"""
        default_set_int.discard(20)
        print(len(default_set_int))
        assert len(default_set_int) == 2
        assert 20 not in default_set_int

    def test_discard_non_existing_element(self, default_set_int):
        """测试移除一个不存在的元素，不应引发错误，长度不应改变。"""
        initial_len = len(default_set_int)
        default_set_int.discard(99)  # 99 不存在
        assert len(default_set_int) == initial_len
        assert 99 not in default_set_int

    def test_iteration(self, default_set_int, test_values_int):
        """测试集合的迭代。"""
        # 将集合转换为列表并检查所有元素
        items = sorted(list(default_set_int))
        assert items == list(test_values_int)

    def test_type_enforcement_on_add(self, empty_set_int):
        """测试尝试添加非整数类型时是否引发 TypeError。"""
        # 使用 pytest.raises 来检查期望的异常
        with pytest.raises(TypeError):
            empty_set_int.add("hello")

        with pytest.raises(TypeError):
            empty_set_int.add(3.14)

    def test_initialization_with_non_int_raises_error(
        self,
    ):
        """测试用非 int 迭代器初始化时是否引发 TypeError。"""
        # 异常应在第一次调用 add() 时发生
        with pytest.raises(TypeError):
            RedisSetInt([1, 2, "a", 4])  # type: ignore

    def test_repr(self, default_set_int, test_values_int):
        """测试 __repr__ 方法。"""
        items = [int(item) for item in repr(default_set_int).split(", ")]
        assert set(items) == set(test_values_int)

    def test_iter(self, default_set_int):
        """测试 __iter__ 方法。"""
        for item in default_set_int:
            assert isinstance(item, int)


@pytest.fixture
def test_values_uuid():
    """返回一个包含三个唯一 UUID 对象的元组。"""
    # 确保每次测试运行时 UUID 都是唯一的
    return (uuid4(), uuid4(), uuid4())


@pytest.fixture
def empty_set_uuid():
    """返回一个空的 UuidMutableSet 实例。"""
    return RedisSetUUID(redis_uri=REDIS_URI)


@pytest.fixture
def default_set_uuid(test_values_uuid):
    """返回一个包含三个 UUID 的实例。"""
    return RedisSetUUID(test_values_uuid, redis_uri=REDIS_URI)


class TestRedisSetUUID:
    def test_initial_set_is_empty(self, empty_set_uuid):
        """测试一个新创建的集合是否为空。"""
        assert len(empty_set_uuid) == 0

    def test_add_and_membership(self, empty_set_uuid, test_values_uuid):
        """测试添加 UUID 对象和成员资格。"""
        u1, u2, _ = test_values_uuid

        empty_set_uuid.add(u1)
        empty_set_uuid.add(u2)

        assert len(empty_set_uuid) == 2
        assert u1 in empty_set_uuid
        assert u2 in empty_set_uuid

    def test_add_duplicate_uuid(self, default_set_uuid, test_values_uuid):
        """测试添加重复 UUID,长度不应改变。"""
        initial_len = len(default_set_uuid)
        u1, _, _ = test_values_uuid

        default_set_uuid.add(u1)  # u1 已经存在
        assert len(default_set_uuid) == initial_len

    def test_discard_existing_uuid(self, default_set_uuid, test_values_uuid):
        """测试移除一个存在的 UUID 元素。"""
        u2 = test_values_uuid[1]

        default_set_uuid.discard(u2)
        assert len(default_set_uuid) == 2
        assert u2 not in default_set_uuid

    def test_discard_non_existing_uuid(self, default_set_uuid):
        """测试移除一个不存在的 UUID, 不应引发错误。"""
        initial_len = len(default_set_uuid)

        # 创建一个新的、不在集合中的 UUID
        new_uuid = uuid4()
        default_set_uuid.discard(new_uuid)

        assert len(default_set_uuid) == initial_len

    def test_iteration_and_contents(self, default_set_uuid, test_values_uuid):
        """测试集合的迭代。"""
        expected = set(test_values_uuid)
        actual = set(default_set_uuid)

        # 因为 UUID 是不可变对象,它们可以被安全地用作 set 元素并进行比较
        assert actual == expected

    def test_iteration(self, default_set_uuid, test_values_uuid):
        """测试集合的迭代。"""
        # 将集合转换为列表并检查所有元素
        items = sorted(list(default_set_uuid))
        assert items == sorted(test_values_uuid)

    def test_initialization_with_non_int_raises_error(
        self,
    ):
        """测试用非 int 迭代器初始化时是否引发 TypeError。"""
        # 异常应在第一次调用 add() 时发生
        with pytest.raises(TypeError):
            RedisSetUUID([uuid4(), uuid4(), 4, "aa"])  # type: ignore

    def test_repr(self, default_set_uuid, test_values_uuid):
        """测试 __repr__ 方法。"""
        items = [UUID(item) for item in repr(default_set_uuid).split(", ")]
        assert set(items) == set(test_values_uuid)
