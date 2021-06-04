"""
Generates files for each of the feature files containing pytest-bdd scenario stubs.
"""
import re
from contextlib import asynccontextmanager
from functools import wraps
from textwrap import dedent
from typing import Any, AsyncGenerator, Callable, Coroutine, List, MutableMapping, Tuple

import trio
from pytest_bdd.parser import parse_feature as _parse_feature  # type: ignore
from trio import Path


def set_result(
    results: MutableMapping[str, Any],
    key: str,
    func: Callable[..., Coroutine[None, None, Any]],
) -> Callable[..., Coroutine[None, None, None]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:
        results[key] = await func(*args, **kwargs)

    return wrapper


class ResultNursery:
    def __init__(self, nursery: trio.Nursery) -> None:
        self.nursery = nursery
        self.results: MutableMapping[str, Any] = {}

    def start_soon_result(
        self, name: str, async_fn: Callable[..., Coroutine[None, None, Any]], *args: Any
    ) -> None:
        self.nursery.start_soon(
            set_result(self.results, name, async_fn), *args, name=name
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self.nursery, name)


@asynccontextmanager
async def open_result_nursery() -> AsyncGenerator[ResultNursery, None]:
    async with trio.open_nursery() as nursery:
        yield ResultNursery(nursery)


async def parse_feature(feature_path: Path) -> Tuple[str, List[str]]:
    feat = await trio.to_thread.run_sync(
        _parse_feature, str((await feature_path.absolute()).parent), feature_path.name
    )
    return (feat.name, list(feat.scenarios.keys()))


def clean(var_str: str) -> str:
    return re.sub(r"\W|^(?=\d)", "_", var_str).lower()


def escape_scenario(scenario: str) -> str:
    return scenario.replace('"', '\\"')


async def generate_feature_stub(feature_path: Path, scenarios: List[str]) -> None:
    this_dir = await Path(__file__).parent.absolute()
    stub_name = "test_%s.py" % feature_path.name.rsplit(".", 1)[0]
    stub_contents = "from pytest_bdd import scenario  # type: ignore\n\n\n"
    stub_contents += "\n\n".join(
        dedent(
            f'''\
            @scenario("{feature_path}", "{escape_scenario(scenario)}")
            def test_{clean(scenario)}() -> None:
                """
                {scenario}
                """
                pass
            '''
        )
        for i, scenario in enumerate(scenarios)
    )
    stub_path = Path.joinpath(this_dir, stub_name)
    print(f"Writing to {stub_path}")
    async with await Path.open(stub_path, "w") as stub_file:
        await stub_file.write(stub_contents)


async def parse_and_generate(feature_path: Path) -> Tuple[str, List[str]]:
    feat_name, scenarios = await parse_feature(feature_path)
    await generate_feature_stub(feature_path, scenarios)
    return feat_name, scenarios


async def main() -> None:
    async with open_result_nursery() as result_nursery:
        for feat_path in await Path.iterdir(Path("features")):
            result_nursery.start_soon_result(
                str(feat_path), parse_and_generate, feat_path
            )

    print(
        "\n\n".join(
            "Feature '%s':\n%s" % (feature, "\n".join(scenarios))
            for feature, scenarios in result_nursery.results.values()
        )
    )

    await trio.run_process(["black", "."])


if __name__ == "__main__":
    trio.run(main)
