import os
from typing import Callable

import pytest

from djinni import Djinni
from djinni.djinni import Lifecycle


def test_with_providers_and_chainable():
    def dummy_fn(providers, debug):
        pass

    dj = Djinni(dummy_fn)
    p1 = lambda: 1
    p2 = lambda: 2
    ret = dj.with_providers([p1, p2])

    assert ret is dj
    assert len(dj.providers) == 2
    assert dj.providers[0] is p1 and dj.providers[1] is p2


def test_with_debug_sets_flag():
    def dummy_fn(providers, debug):
        pass

    # default when env var not set
    env_backup = os.environ.pop('DEBUG_DJINNI', None)
    try:
        dj = Djinni(dummy_fn)
        assert dj.debug is False
    finally:
        if env_backup is not None:
            os.environ['DEBUG_DJINNI'] = env_backup

    # when env var set to true
    os.environ['DEBUG_DJINNI'] = '1'
    try:
        dj2 = Djinni(dummy_fn)
        assert dj2.debug is True
    finally:
        os.environ.pop('DEBUG_DJINNI', None)


def test_run_calls_function_with_providers_and_debug():
    # provider must declare its return type; the called function must
    # declare the parameter type to receive the provided value
    called = []

    def fn(value: str):
        called.append(value)

    def provider() -> str:
        return 'x'

    dj = Djinni(fn)
    dj.with_providers([provider])
    dj.with_auto_shutdown(True)
    dj.run()

    assert called == ['x']


def test_with_importer_supplies_providers():
    called = []

    def fn(value: int):
        called.append(value)

    class SimpleImporter:
        def import_providers(self, t: type, adder):
            if t is int:
                def prov() -> int:
                    return 42
                adder.add_providers([prov])

    dj = Djinni(fn)
    dj.with_importer(SimpleImporter())
    dj.with_auto_shutdown(True)
    dj.run()

    assert called == [42]


def test_lifecycle_injection_and_hooks():
    called = []

    def main(l: Lifecycle):
        def onstart():
            called.append('start')

        def onstop():
            called.append('stop')

        l.hook(onstart, onstop)

    dj = Djinni(main)
    dj.with_auto_shutdown(True)
    dj.run()

    assert called == ['start', 'stop']


def test_provider_tuple_return_caches_all_and_returns_requested_type():
    called = []

    def fn(value: int):
        called.append(value)

    def provider() -> tuple[int, str]:
        return (7, 'seven')

    dj = Djinni(fn)
    dj.with_providers([provider])
    dj.with_auto_shutdown(True)
    dj.run()

    assert called == [7]
    assert dj.instances.get(int) == 7
    assert dj.instances.get(str) == 'seven'


def test_colored_provider_synthesis():
    from typing import TypeVar
    from djinni.djinni import Color

    called = []
    Green = TypeVar('Green')
    GreenInt = Color[int, Green]
    GreenStr = Color[str, Green]

    def print_green_int(ig: GreenInt):
        called.append(ig.value)

    def atoi(s: str) -> int:
        return int(s)

    dj = Djinni(print_green_int)
    dj.with_providers([atoi])
    dj.with_instances({GreenStr: Color('7')})
    dj.with_auto_shutdown(True)
    dj.run()

    assert called == [7]


def test_listcollection_provider_collects_all():
    from djinni.djinni import ListCollection

    collected = []

    def consume_all(vals: ListCollection[int]):
        collected.append(list(vals.items))

    def p1() -> int:
        return 1

    def p2() -> int:
        return 2

    dj = Djinni(consume_all)
    dj.with_providers([p1, p2])
    dj.with_auto_shutdown(True)
    dj.run()

    assert collected == [[1, 2]]


def test_color_marker_distinction():
    from typing import TypeVar
    from djinni.djinni import Color

    called_g = []
    called_b = []
    Green = TypeVar('Green')
    Blue = TypeVar('Blue')

    def main(g: Color[int, Green], b: Color[int, Blue]):
        called_g.append(g.value)
        called_b.append(b.value)

    def p() -> int:
        return 5

    dj = Djinni(main)
    dj.with_providers([p])
    dj.with_auto_shutdown(True)
    dj.run()

    assert called_g == [5] and called_b == [5]
    assert Color[int, Green] in dj.instances
    assert Color[int, Blue] in dj.instances


def test_marker_mismatch_does_not_unwrap_other_marker():
    from typing import TypeVar
    from djinni.djinni import Color

    called = []
    Green = TypeVar('Green')
    Blue = TypeVar('Blue')

    # store a Green-colored int
    dj = Djinni(lambda c: None)
    dj.with_instances({Color[int, Green]: Color(9)})

    def prov() -> int:
        return 3

    def main(c: Color[int, Blue]):
        called.append(c.value)

    dj = Djinni(main)
    dj.with_instances({Color[int, Green]: Color(9)})
    dj.with_providers([prov])
    dj.with_auto_shutdown(True)
    dj.run()

    # provider exists so Blue should be synthesized from provider (3), not from stored Green (9)
    assert called == [3]


def test_listcollection_interface_elements():
    from typing import Protocol, runtime_checkable
    from djinni.djinni import ListCollection

    @runtime_checkable
    class Valuer(Protocol):
        def value(self) -> int: ...

    class A:
        def __init__(self, v: int):
            self._v = v
        def value(self) -> int:
            return self._v

    class B:
        def __init__(self, v: int):
            self._v = v
        def value(self) -> int:
            return self._v

    collected = []

    def consume(vals: ListCollection[Valuer]):
        collected.append([it.value() for it in vals.items])

    def p1() -> Valuer:
        return A(1)

    def p2() -> Valuer:
        return B(2)

    dj = Djinni(consume)
    dj.with_providers([p1, p2])
    dj.with_auto_shutdown(True)
    dj.run()

    assert collected == [[1, 2]]
    


def test_listcollection_type_separation():
    from djinni.djinni import ListCollection

    collected_ints = []
    collected_strs = []

    def main(li: ListCollection[int], ls: ListCollection[str]):
        collected_ints.append(list(li.items))
        collected_strs.append(list(ls.items))

    def p1() -> int:
        return 1

    def p2() -> str:
        return "a"

    dj = Djinni(main)
    dj.with_providers([p1, p2])
    dj.with_auto_shutdown(True)
    dj.run()

    assert collected_ints == [[1]]
    assert collected_strs == [["a"]]


def test_find_providers_does_not_call_importer_when_providers_match():
    called = []

    def fn(v: int):
        called.append(v)

    def p() -> int:
        return 99

    class RecorderImporter:
        def __init__(self):
            self.called = False
        def import_providers(self, t: type, adder):
            self.called = True
            def prov() -> int:
                return 42
            adder.add_providers([prov])

    imp = RecorderImporter()

    dj = Djinni(fn)
    dj.with_providers([p])
    dj.with_importer(imp)
    dj.with_auto_shutdown(True)
    dj.run()

    assert called == [99]
    assert imp.called is False


def test_add_provider_module_and_decorator_collects_decorated_functions():
    import types
    called = []

    def main(v: int):
        called.append(v)

    from djinni import Djinni
    from djinni.djinni import provider

    # create a fake module and attach one decorated and one plain function
    m = types.ModuleType("m_testmod")

    def prov() -> int:
        return 123

    def other() -> int:
        return 999

    # mark prov as a provider and attach both to the module
    prov = provider(prov)
    setattr(m, "prov", prov)
    setattr(m, "other", other)

    dj = Djinni(main)
    # add providers from the module
    dj.add_provider_module(m)
    dj.with_auto_shutdown(True)
    dj.run()

    # only the decorated provider should have been collected
    assert called == [123]


def test_find_providers_uses_importer_when_no_providers_match():
    called = []

    def fn(v: int):
        called.append(v)

    class RecorderImporter:
        def __init__(self):
            self.called = False
        def import_providers(self, t: type, adder):
            self.called = True
            def prov() -> int:
                return 42
            adder.add_providers([prov])

    imp = RecorderImporter()

    dj = Djinni(fn)
    dj.with_importer(imp)
    dj.with_auto_shutdown(True)
    dj.run()

    assert called == [42]
    assert imp.called is True


def test_instances_prevent_importer_and_use_instances_for_color():
    from typing import TypeVar
    from djinni.djinni import Color

    called = []

    def fn(v: int):
        called.append(v)

    class RecorderImporter:
        def __init__(self):
            self.called = False
        def import_providers(self, t: type, adder):
            self.called = True
            def prov() -> int:
                return 42
            adder.add_providers([prov])

    imp = RecorderImporter()

    # case 1: instance for int present -> importer not called
    dj = Djinni(fn)
    dj.with_instances({int: 7})
    dj.with_importer(imp)
    dj.with_auto_shutdown(True)
    dj.run()
    assert called == [7]
    assert imp.called is False

    # case 2: instance for Color[int,Marker] present -> used directly
    called2 = []
    Marker = TypeVar('Marker')
    def main_color(c: Color[int, Marker]):
        called2.append(c.value)

    dj2 = Djinni(main_color)
    dj2.with_instances({Color[int, Marker]: Color(9)})
    dj2.with_importer(imp)
    dj2.with_auto_shutdown(True)
    dj2.run()
    assert called2 == [9]
    assert imp.called is False
