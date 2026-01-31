import functools
import inspect
from typing import (
    Any,
    Callable,
    Coroutine,
    Generator,
    Generic,
    List,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)

import trio
from typing_extensions import Self

# Parameter specification for execution functions
P = ParamSpec("P")
# Execution result type
R = TypeVar("R")
# Parent execution result type
U = TypeVar("U")
# Next execution result type
K = TypeVar("K")


class LazyExecutionNode(Generic[P, R]):
    """
    Lazy asynchronous execution node.

    Represents a single step in an execution chain. Each node wraps an
    asynchronous callable and may reference a parent node whose result
    is used as input.

    Execution is deferred until the node is awaited. When awaited, the
    entire chain is resolved sequentially from the root to the current
    node.
    """

    def __init__(
        self,
        fn: Callable[P, Coroutine[None, None, R]],
        *,
        parent: "LazyExecutionNode[..., U] | None" = None,
    ) -> None:
        self._fn = fn
        self._parent: "LazyExecutionNode[Any, Any] | None" = parent
        self._head: Coroutine[None, None, R] | None = None

    def __await__(self) -> Generator[None, None, R]:
        current = self
        nodes: List[LazyExecutionNode[P, R]] = []
        while current is not None:
            nodes.append(current)
            current = current._parent

        async def execute() -> R:
            result = None
            async with trio.open_nursery():
                while nodes:
                    node = nodes.pop()
                    if node._head is not None:
                        result = await node._head
                        continue
                    signature = inspect.signature(node._fn)
                    if result is None:
                        bound = signature.bind()
                    else:
                        bound = signature.bind(result)
                    result = await node._fn(*bound.args, **bound.kwargs)
            return cast(R, result)

        return execute().__await__()

    def attach(self, parent: "LazyExecutionNode[..., U]") -> Self:
        self._parent = parent
        return self

    @overload
    def then(
        self,
        nxt: Callable[[R], Coroutine[None, None, K]],
        **kwargs: Any,
    ) -> "LazyExecutionNode[[R], K]": ...

    @overload
    def then(
        self,
        nxt: Callable[[], Coroutine[None, None, K]],
        **kwargs: Any,
    ) -> "LazyExecutionNode[[R], K]": ...

    def then(
        self,
        nxt: Callable[..., Coroutine[None, None, K]],
        **kwargs: Any,
    ) -> "LazyExecutionNode[[R], K]":
        """
        Appends a new execution node to the chain.

        The provided callable is wrapped and executed after the current
        node resolves. Keyword arguments are bound eagerly.

        Args:
            nxt: Asynchronous callable executed after this node.
            **kwargs: Keyword arguments bound to the callable.

        Returns:
            A new lazy execution node attached to the current one.

        Raises:
            RuntimeError: If the root node has not been initialized.
        """

        if self._parent is None and self._head is None:
            raise RuntimeError(
                "Cannot chain a root execution node that is not initialized."
            )

        nxt = functools.partial(nxt, **kwargs)
        return LazyExecutionNode[[R], K](nxt, parent=self)


class LazyExecutionChain(LazyExecutionNode[P, R]):
    """
    Root execution chain entry point.

    Represents the starting node of a lazy execution chain. The chain
    remains inert until explicitly initialized and awaited.
    """

    def __init__(self, fn: Callable[P, Coroutine[None, None, R]]) -> None:
        super().__init__(fn, parent=None)
        self._head: Coroutine[None, None, R] | None = None

    def init(self, *args: P.args, **kwargs: P.kwargs) -> Self:
        """
        Initializes the execution chain.

        Binds arguments to the root callable and prepares the chain
        for execution.

        Args:
            *args: Positional arguments passed to the root callable.
            **kwargs: Keyword arguments passed to the root callable.

        Returns:
            The initialized execution chain.

        Raises:
            RuntimeError: If the chain has already been attached to a parent.
        """

        if self._parent is not None:
            raise RuntimeError("Cannot initialize an execution chain directly.")
        self._head = self._fn(*args, **kwargs)
        return self
