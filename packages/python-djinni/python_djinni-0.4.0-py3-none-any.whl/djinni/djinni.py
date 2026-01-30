from __future__ import annotations
import os
from typing import Sequence, Callable, Dict, Any, Protocol, Optional, get_origin, get_args, TypeVar, Generic
import inspect
import time
import threading
import sys

class Lifecycle(Protocol):
    def hook(self, onstart: Optional[Callable], onstop: Optional[Callable]) -> None:
        """Register optional startup and shutdown callables."""
        pass
    def shutdown(self) -> None:
        """Signal shutdown: implementations should set a stop flag."""
        pass


class Importer(Protocol):
    def import_providers(self, t: type, adder: "ProviderAdder") -> None:
        pass


class ProviderAdder(Protocol):
    def add_providers(self, providers: Sequence[Callable]) -> None:
        pass
    def add_provider_module(self, module: Any) -> None:
        pass


def provider(fn: Callable) -> Callable:
    """Decorator to mark a function as a provider for module scanning.

    Use on top-level functions in a module. `add_provider_module` will
    collect functions decorated with `@provider`.
    """
    setattr(fn, "__djinni_provider__", True)
    return fn


# Generic Color wrapper: Color[T, Marker] wraps a value of type T and carries a marker type
T = TypeVar('T')
M = TypeVar('M')
class Color(Generic[T, M]):
    def __init__(self, value: T):
        self.value: T = value
    def __repr__(self) -> str:  # helpful for debug
        return f"Color({self.value!r})"


# Generic ListCollection wrapper: ListCollection[T] holds a list of T
U = TypeVar('U')
class ListCollection(Generic[U]):
    def __init__(self, items: list[U]):
        self.items: list[U] = list(items)
    def __repr__(self) -> str:
        return f"ListCollection({self.items!r})"

def make_wrapper(base_fn, base_sig, marker_type):
    # wrapper executes by binding incoming args to the base signature,
    # unwrapping any Color values, calling the base function, and
    # re-wrapping the result in Color.
    def wrapper(*args, **kwargs):
        bound = base_sig.bind_partial(*args, **kwargs)
        # prepare positional and keyword args for base_fn
        call_args = []
        call_kwargs = {}
        for name, param in base_sig.parameters.items():
            if name not in bound.arguments:
                continue
            val = bound.arguments[name]
            unwrapped = getattr(val, 'value', val)
            if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                call_args.append(unwrapped)
            elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                call_args.extend(unwrapped)
            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                call_kwargs[name] = unwrapped
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                call_kwargs.update(unwrapped)

        res = base_fn(*call_args, **call_kwargs)
        return Color(res)

    # build a Signature for the wrapper that matches the base signature but
    # uses Color[...] annotations for parameters and return type
    new_params = []
    for name, param in base_sig.parameters.items():
        ann = param.annotation
        if ann is not inspect._empty:
            try:
                new_ann = Color[ann, marker_type]
            except Exception:
                new_ann = ann
        else:
            new_ann = inspect._empty

        new_param = inspect.Parameter(name, param.kind, default=param.default, annotation=new_ann)
        new_params.append(new_param)

    # return annotation
    ret = base_sig.return_annotation
    if ret is not inspect._empty:
        try:
            new_ret = Color[ret, marker_type]
        except Exception:
            new_ret = ret
    else:
        new_ret = inspect._empty

    wrapper.__signature__ = inspect.Signature(parameters=new_params, return_annotation=new_ret)
    wrapper.__name__ = f"{getattr(base_fn, '__name__', 'provider')}_{getattr(marker_type, '__name__', str(marker_type))}"
    return wrapper

class Djinni:
    def __init__(self, fn):
        self.fn = fn
        self.providers: list[Callable] = []
        self.importer: Optional[Importer] = None
        self.onstart: list[Callable] = []
        self.onstop: list[Callable] = []
        self.stop: bool = False
        self._stop_event = threading.Event()
        self.auto_shutdown: bool = False
        self.auto_kill: bool = False
        self.debug = 'DEBUG_DJINNI' in os.environ and os.environ['DEBUG_DJINNI'].lower() in ('1', 'true')
        self.instances: dict[type, object] = {}
        # make lifecycle available for injection
        self.instances[Lifecycle] = self

    def add_providers(self, providers: Sequence[Callable]) -> None:
        """ProviderAdder implementation: add providers to the Djinni registry."""
        for p in providers:
            if p not in self.providers:
                self.providers.append(p)

    def add_provider_module(self, module: Any) -> None:
        """Collect functions decorated with `@provider` from `module` and add them.

        `module` should be a module object; this scans its attributes and
        collects callables with the `__djinni_provider__` marker set by
        the `@provider` decorator, then forwards them to `add_providers`.
        """
        collected: list[Callable] = []
        for name in dir(module):
            try:
                attr = getattr(module, name)
            except Exception:
                continue
            if callable(attr) and getattr(attr, "__djinni_provider__", False):
                collected.append(attr)
        if collected:
            self.add_providers(collected)

    def with_providers(self, providers: Sequence[Callable]) -> Djinni:
        "providers provide dependencies, each function must provide type hints for the required input types and return value types"
        self.providers.extend(providers)
        if self.debug:
            print(f"Djinni.with_providers: added {len(providers)} providers")
        return self

    def with_instances(self, instances: Dict[type,object]) -> Djinni:
        self.instances.update(instances)
        return self

    def with_importer(self, importer: Importer) -> Djinni:
        self.importer = importer
        if self.debug:
            print(f"Djinni.with_importer: registered importer {importer!r}")
        return self

    def with_debug(self, debug: bool) -> Djinni:
        "set debug flag"
        self.debug = debug
        return self

    def with_auto_shutdown(self, auto: bool) -> Djinni:
        """Enable or disable automatic shutdown (skip wait loop)."""
        self.auto_shutdown = bool(auto)
        return self

    def with_auto_kill(self, auto: bool) -> Djinni:
        """Enable or disable automatic kill after timeout."""
        self.auto_kill = bool(auto)
        return self

    def hook(self, onstart: Optional[Callable], onstop: Optional[Callable]) -> None:
        """Implement `Lifecycle.hook` to register lifecycle callbacks."""
        if onstart:
            self.onstart.append(onstart)
            if self.debug:
                print(f"Djinni.hook: registered onstart {onstart!r}")
        if onstop:
            self.onstop.append(onstop)
            if self.debug:
                print(f"Djinni.hook: registered onstop {onstop!r}")

    def shutdown(self) -> None:
        """Implement `Lifecycle.shutdown` to request shutdown."""
        if not self.stop:
            self.stop = True
            # wake any waiting run() call
            self._stop_event.set()

    def _find_providers(self, t: type, all: bool = False) -> list[Callable]:
        """Return a list of providers that can produce type `t`.

        If `all` is False the list may contain at most one (first) provider.
        """
        if self.debug:
            print(f"Djinni._find_providers: looking for providers for type {t} (all={all})")

        matches: list[Callable] = []
        # scan existing providers
        for provider in self.providers:
            sig = inspect.signature(provider)
            ret_anno = sig.return_annotation
            if ret_anno is t:
                matches.append(provider)
                if not all:
                    return matches
                continue
            # support providers returning multiple typed values as a tuple
            origin = get_origin(ret_anno)
            args = get_args(ret_anno)
            if origin is tuple and args and t in args:
                matches.append(provider)
                if not all:
                    return matches
            # one is enough
            if matches:
                return matches

        # consult importer to load more providers (new API: importer is passed a ProviderAdder)
        if self.importer:
            if self.debug:
                print(f"Djinni._find_providers: consulting importer for {t}")
            # snapshot existing providers so we can detect newly added ones
            old_providers = list(self.providers)
            try:
                # pass self which implements ProviderAdder.add_providers
                self.importer.import_providers(t, self)
            except Exception:
                pass

            # determine which providers were added by the importer
            new_providers = [p for p in self.providers if p not in old_providers]
            if new_providers:
                # re-scan providers for matches
                for provider in new_providers:
                    sig = inspect.signature(provider)
                    ret_anno = sig.return_annotation
                    if ret_anno is t:
                        matches.append(provider)
                        if not all:
                            return matches
                        continue
                    origin = get_origin(ret_anno)
                    args = get_args(ret_anno)
                    if origin is tuple and args and t in args:
                        matches.append(provider)
                        if not all:
                            return matches
            # one is enough
            if matches:
                return matches

        # synthesize colored providers for Color[...] requests
        try:
            req_origin = get_origin(t)
            req_args = get_args(t)
        except Exception:
            req_origin = None
            req_args = ()

        if req_origin is Color and req_args:
            underlying = req_args[0]
            marker = req_args[1] if len(req_args) > 1 else None
            base_list = self._find_providers(underlying, all=False)
            if base_list:
                base = base_list[0]
                wrapper = make_wrapper(base, inspect.signature(base), marker)
                self.providers.append(wrapper)
                matches.append(wrapper)
                if not all:
                    return matches

        # synthesize list-collection providers for ListCollection[...] requests
        if req_origin is ListCollection and req_args:
            underlying = req_args[0]
            # create provider that collects all providers for underlying
            def list_provider():
                items = []
                provs = self._find_providers(underlying, all=True)
                for p in provs:
                    items.append(self._call_fn(p))
                return ListCollection(items)

            # set signature: no params, return ListCollection[underlying]
            list_provider.__signature__ = inspect.Signature(parameters=[], return_annotation=t)
            self.providers.append(list_provider)
            matches.append(list_provider)
            if not all:
                return matches

        if self.debug:
            print(f"Djinni._find_providers: found {len(matches)} providers for {t}")
        return matches

    def _get_type(self, t: type) -> Any:
        if t in self.instances:
            if self.debug:
                print(f"Djinni._get_type: returning instance for {t}")
            return self.instances[t]
        providers = self._find_providers(t, all=False)
        if not providers:
            return None
        provider = providers[0]
        # call provider to get a result
        result = self._call_fn(provider)
        # inspect provider return annotation to support tuple returns
        sig = inspect.signature(provider)
        ret_anno = sig.return_annotation
        origin = get_origin(ret_anno)
        args = get_args(ret_anno)
        if origin is tuple and args:
            for i, argtype in enumerate(args):
                if i < len(result):
                    self.instances[argtype] = result[i]
                    if self.debug:
                        print(f"Djinni._get_type: cached instance for {argtype}: {result[i]!r}")
        else:
            self.instances[t] = result
            if self.debug:
                print(f"Djinni._get_type: cached instance for {t}: {result!r}")
        if t not in self.instances:
            return None
        result = self.instances[t]
        return result

    def _call_fn(self, fn: Callable) -> Any:
        if not fn:
            return None
        sig = inspect.signature(fn)
        args: list[Any] = []
        for name, param in sig.parameters.items():
            anno = param.annotation
            if anno is inspect._empty:
                value = None
            elif anno not in self.instances:
                value = self._get_type(anno)
            else:
                value = self.instances[anno]
            args.append(value)

        if self.debug:
            print(f"Djinni._call_fn: calling {getattr(fn, '__name__', repr(fn))} with args={args}")
        result = fn(*args)
        if self.debug:
            print(f"Djinni._call_fn: {getattr(fn, '__name__', repr(fn))} returned {result!r}")
        return result

    def run(self) -> None:
        if self.debug:
            print(f"Djinni.run: starting run (auto_shutdown={self.auto_shutdown}, auto_kill={self.auto_kill})")

        # call main function
        if self.debug:
            print("Djinni.run: calling main function")
        self._call_fn(self.fn)

        # run startup hooks
        if self.debug:
            print(f"Djinni.run: running {len(self.onstart)} startup hooks")
        for fn in self.onstart:
            self._call_fn(fn)

        # record baseline thread count after startup hooks
        baseline_threads = threading.active_count()
        if self.debug:
            print(f"Djinni.run: baseline thread count={baseline_threads}")

        # wait until shutdown is requested (unless auto_shutdown enabled)
        if not self.auto_shutdown:
            if self.debug:
                print("Djinni.run: waiting for shutdown event")
            # block until shutdown() sets the event
            self._stop_event.wait()
        else:
            if self.debug:
                print("Djinni.run: auto_shutdown enabled, skipping wait loop")

        # run shutdown hooks
        if self.debug:
            print(f"Djinni.run: running {len(self.onstop)} shutdown hooks")
        for fn in self.onstop:
            self._call_fn(fn)

        # ensure process can exit: wait until active thread count returns to baseline
        start = time.time()
        if self.debug:
            print("Djinni.run: waiting for threads to return to baseline...")
        while threading.active_count() > baseline_threads:
            elapsed = time.time() - start
            if self.debug:
                print(f"Djinni.run: active_count={threading.active_count()} elapsed={elapsed:.1f}s")
            if elapsed > 5 and self.auto_kill:
                if self.debug:
                    print("Djinni.run: auto_kill timeout reached; exiting")
                sys.exit(1)
            time.sleep(0.5)
        if self.debug:
            print("Djinni.run: exiting run")
