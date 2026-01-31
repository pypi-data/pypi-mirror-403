"""Tests for the lazy evaluation library."""

import json

import pytest

from lazyval import Lazy, LazyJSONEncoder, dumps, lazy, lazy_json_default, loads


class TestLazyBasics:
    """Core lazy evaluation functionality."""

    def test_deferred_evaluation(self):
        calls = []
        lazy_val = Lazy(lambda: calls.append(1) or 42)
        assert calls == []
        assert lazy_val == 42
        assert calls == [1]

    def test_cached_evaluation(self):
        calls = []
        lazy_val = Lazy(lambda: calls.append(1) or 42)
        _ = lazy_val + 0
        _ = lazy_val + 0
        assert len(calls) == 1

    def test_is_evaluated_property(self):
        lazy_val = Lazy(lambda: 42)
        assert not lazy_val.is_evaluated
        lazy_val.force()
        assert lazy_val.is_evaluated

    def test_force_method(self):
        lazy_val = Lazy(lambda: 42)
        assert lazy_val.force() == 42

    def test_non_callable_raises(self):
        with pytest.raises(TypeError, match="Expected callable"):
            Lazy(42)  # type: ignore


class TestStringRepresentation:
    """String formatting and representation."""

    def test_str(self):
        assert str(Lazy(lambda: "hello")) == "hello"

    def test_repr_unevaluated(self):
        lazy_val = Lazy(lambda: 42)
        assert "unevaluated" in repr(lazy_val)

    def test_repr_evaluated(self):
        lazy_val = Lazy(lambda: 42)
        lazy_val.force()
        assert repr(lazy_val) == "42"

    def test_format(self):
        assert f"{Lazy(lambda: 3.14159):.2f}" == "3.14"


class TestComparisons:
    """Comparison operators."""

    def test_eq(self):
        assert Lazy(lambda: 42) == 42
        assert Lazy(lambda: 42) == Lazy(lambda: 42)

    def test_lt_gt(self):
        assert Lazy(lambda: 10) < 20
        assert Lazy(lambda: 20) > 10

    def test_le_ge(self):
        assert Lazy(lambda: 10) <= 10
        assert Lazy(lambda: 10) >= 10


class TestArithmetic:
    """Arithmetic operations."""

    def test_basic_ops(self):
        lazy_val = Lazy(lambda: 10)
        assert lazy_val + 5 == 15
        assert lazy_val - 3 == 7
        assert lazy_val * 2 == 20
        assert lazy_val / 2 == 5.0
        assert lazy_val // 3 == 3
        assert lazy_val % 3 == 1
        assert lazy_val**2 == 100

    def test_reverse_ops(self):
        lazy_val = Lazy(lambda: 10)
        assert 15 - lazy_val == 5
        assert 20 / lazy_val == 2.0

    def test_unary_ops(self):
        lazy_val = Lazy(lambda: -5)
        assert -lazy_val == 5
        assert abs(lazy_val) == 5

    def test_lazy_with_lazy(self):
        a = Lazy(lambda: 10)
        b = Lazy(lambda: 5)
        assert a + b == 15


class TestContainerOps:
    """Container and iteration support."""

    def test_getitem(self):
        lazy_dict = Lazy(lambda: {"a": 1, "b": 2})
        assert lazy_dict["a"] == 1

    def test_setitem(self):
        lazy_list = Lazy(lambda: [1, 2, 3])
        lazy_list[0] = 99
        assert lazy_list[0] == 99

    def test_len(self):
        assert len(Lazy(lambda: [1, 2, 3])) == 3

    def test_iter(self):
        assert list(Lazy(lambda: [1, 2, 3])) == [1, 2, 3]

    def test_contains(self):
        assert 2 in Lazy(lambda: [1, 2, 3])


class TestAttributeAccess:
    """Attribute access delegation."""

    def test_getattr(self):
        lazy_str = Lazy(lambda: "hello")
        assert lazy_str.upper() == "HELLO"

    def test_private_attr_raises(self):
        lazy_val = Lazy(lambda: 42)
        with pytest.raises(AttributeError):
            _ = lazy_val._nonexistent


class TestTypeConversions:
    """Type conversion support."""

    def test_bool(self):
        assert bool(Lazy(lambda: 1)) is True
        assert bool(Lazy(lambda: 0)) is False

    def test_int(self):
        assert int(Lazy(lambda: 3.14)) == 3

    def test_float(self):
        assert float(Lazy(lambda: 42)) == 42.0

    def test_hash(self):
        assert hash(Lazy(lambda: "hello")) == hash("hello")


class TestCallable:
    """Callable wrapper support."""

    def test_call(self):
        lazy_func = Lazy(lambda: lambda x: x * 2)
        assert lazy_func(21) == 42


class TestDecorator:
    """Lazy decorator usage."""

    def test_lazy_decorator(self):
        @lazy
        def expensive():
            return 42

        assert expensive == 42


class TestJSON:
    """JSON serialization support."""

    def test_dumps_with_default(self):
        data = {"value": Lazy(lambda: 42)}
        result = json.dumps(data, default=lazy_json_default)
        assert json.loads(result) == {"value": 42}

    def test_dumps_with_encoder(self):
        data = {"value": Lazy(lambda: 42)}
        result = json.dumps(data, cls=LazyJSONEncoder)
        assert json.loads(result) == {"value": 42}

    def test_convenience_dumps(self):
        data = {"value": Lazy(lambda: 42)}
        result = dumps(data)
        assert json.loads(result) == {"value": 42}

    def test_nested_lazy(self):
        data = {"nested": {"value": Lazy(lambda: "hello")}}
        result = dumps(data)
        assert json.loads(result) == {"nested": {"value": "hello"}}

    def test_loads(self):
        assert loads('{"a": 1}') == {"a": 1}


class TestYAML:
    """YAML serialization support (requires pyyaml)."""

    @pytest.fixture
    def yaml_module(self):
        pytest.importorskip("yaml")
        import yaml

        return yaml

    def test_yaml_dump(self, yaml_module):
        data = {"value": Lazy(lambda: 42)}
        result = yaml_module.dump(data)
        assert yaml_module.safe_load(result) == {"value": 42}

    def test_yaml_nested(self, yaml_module):
        data = {"nested": {"value": Lazy(lambda: "hello")}}
        result = yaml_module.dump(data)
        assert yaml_module.safe_load(result) == {"nested": {"value": "hello"}}


class TestJinja2:
    """Jinja2 template rendering support."""

    @pytest.fixture
    def jinja2_module(self):
        pytest.importorskip("jinja2")
        import jinja2

        return jinja2

    def test_template_render(self, jinja2_module):
        template = jinja2_module.Template("Hello, {{ name }}!")
        lazy_name = Lazy(lambda: "World")
        result = template.render(name=lazy_name)
        assert result == "Hello, World!"

    def test_template_with_lazy_dict(self, jinja2_module):
        template = jinja2_module.Template("{{ user.name }} scored {{ user.score }}")
        lazy_user = Lazy(lambda: {"name": "Alice", "score": 95})
        result = template.render(user=lazy_user)
        assert result == "Alice scored 95"

    def test_template_with_lazy_in_loop(self, jinja2_module):
        template = jinja2_module.Template("{% for item in items %}{{ item }},{% endfor %}")
        lazy_items = Lazy(lambda: [1, 2, 3])
        result = template.render(items=lazy_items)
        assert result == "1,2,3,"
