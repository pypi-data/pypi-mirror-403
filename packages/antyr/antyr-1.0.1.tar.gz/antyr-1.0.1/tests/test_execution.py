import pytest
import trio

from antyr.execution import LazyExecutionChain


@pytest.mark.trio
async def test_lazy_execution():
    async def fn():
        return 1

    chain = LazyExecutionChain(fn)
    chain.init()

    result = await chain
    assert result == 1


@pytest.mark.trio
async def test_chain_execution_order():
    async def first():
        return 1

    async def second(x):
        return x + 1

    async def third(x):
        return x * 2

    chain = LazyExecutionChain(first).init().then(second).then(third)
    result = await chain
    assert result == 4


@pytest.mark.trio
async def test_chain_error_propagation():
    async def first():
        return 1

    async def boom(x):
        raise RuntimeError("fail")

    async def never_called(x):
        pass

    with pytest.raises(ExceptionGroup):
        await LazyExecutionChain(first).init().then(boom).then(never_called)


def test_chain_without_init_fails():
    async def fn():
        return 1

    async def second(x):
        return x + 1

    with pytest.raises(RuntimeError):
        LazyExecutionChain(fn).then(second)


@pytest.mark.trio
async def test_chain_with_no_args():

    async def first():
        pass

    async def second():
        return 2

    result = await LazyExecutionChain(first).init().then(second)
    assert result == 2


@pytest.mark.trio
async def test_chain_does_not_spawn_parallel_tasks():
    running = False

    async def fn():
        nonlocal running
        assert running is False
        running = True
        await trio.sleep(0)
        running = False
        return 1

    chain = LazyExecutionChain(fn).init()

    await chain


@pytest.mark.trio
async def test_attach_existing_node():

    async def first():
        return 1

    async def second(x):
        return x + 1

    node = LazyExecutionChain(first).init()
    node = LazyExecutionChain(second).attach(node)
    result = await node
    assert result == 2
