import ast
import json
import os
import pathlib
import shutil
import textwrap
from importlib import import_module
from os.path import join
from typing import Any, Dict, List, Optional, Tuple

import yaml
from ast_to_xml import module_source
from jinja2 import Template

from mqtt_io.types import ConfigType

THIS_DIR = pathlib.Path(__file__).parent.absolute()
CONFIG_SCHEMA_PATH = join(THIS_DIR, "mqtt_io/config/config.schema.yml")
README_TEMPLATE = join(THIS_DIR, "README.md.j2")
MODULES_DIR = join(THIS_DIR, "mqtt_io/modules")

DOCS_DIR = join(THIS_DIR, "docs")
SIDEBAR_TEMPLATE = join(DOCS_DIR, "_sidebar.md.j2")
CONTENT_TEMPLATE = join(DOCS_DIR, "config/reference.md.j2")
MODULES_DOC_TEMPLATE = join(DOCS_DIR, "dev/modules/README.md.j2")
REF_ENTRIES: List[Dict[str, Any]] = []


# TODO: Tasks pending completion -@flyte at 07/03/2021, 11:35:42
# Generate list of supported hardware from the modules themselves.


def title_id(entry_name: str, parents: List[str]) -> str:
    tid = ""
    if parents:
        tid += ("-".join(parents)) + "-"
    tid += entry_name
    return tid.replace("*", "star")


class ConfigSchemaParser:
    @staticmethod
    def parse_schema_section(
        section: ConfigType,
        container: List[Dict[str, Any]],
        parents: Optional[List[str]] = None,
    ) -> None:
        if parents is None:
            parents = []
        else:
            parents = parents.copy()

        child_schema = section.get("schema")
        if child_schema:
            parents.append("*")
            ConfigSchemaParser.parse_schema_section(child_schema, container, parents)
            return

        for entry_name in section.keys():
            entry: ConfigType = section[entry_name]
            ConfigSchemaParser.parse_cerberus_section(
                entry_name, entry, container, parents
            )

    @staticmethod
    def parse_cerberus_section(
        entry_name: str,
        section: ConfigType,
        container: List[Dict[str, Any]],
        parents: List[str],
    ) -> None:
        parents = parents.copy()
        child_schema = section.get("schema")

        children: List[Dict[str, Any]] = []
        toplevel_name = parents[0] if parents else entry_name

        depth = len([x for x in parents if x != "*"])
        tid = title_id(entry_name, parents)
        section.setdefault("meta", {})["title_id"] = tid
        path = f"config/reference/{toplevel_name}/"
        if parents:
            path += f"?id={tid}"
        parents_str = ".".join(parents).replace("*", "&ast;")
        entry_str = entry_name.replace("*", "&ast;")
        subtitle = f"*{parents_str}*.**{entry_str}**" if parents else None

        entry = dict(
            toplevel_name=toplevel_name,
            title=entry_name if entry_name != "*" else f"{parents[-1]}.*",
            subtitle=subtitle,
            entry_name=entry_name,
            element_id=tid,
            depth=depth,
            path=path,
            schema=section,
            meta=section.get("meta", {}),
        )
        container.append(entry)
        REF_ENTRIES.append(entry)

        if child_schema:
            parents.append(entry_name)
            if "type" in child_schema:
                ConfigSchemaParser.parse_cerberus_section(
                    "*", child_schema, children, parents
                )
            else:
                ConfigSchemaParser.parse_schema_section(child_schema, children, parents)


def generate_readmes() -> None:
    blacklist = ("__init__", "mock", "stdio")
    modules_and_titles = (
        ("gpio", "GPIO Modules"),
        ("sensor", "Sensors"),
        ("stream", "Streams"),
    )
    module_strings: Dict[str, Dict[str, str]] = {}
    for module_type, title in modules_and_titles:
        for file_name, ext in [
            os.path.splitext(x) for x in os.listdir(join(MODULES_DIR, module_type))
        ]:
            if ext != ".py" or file_name in blacklist:
                continue
            with open(join(MODULES_DIR, module_type, file_name + ext)) as module_file:
                parsed = ast.parse(module_file.read())
            expr = parsed.body[0]
            assert (
                expr.lineno == 1
                and isinstance(expr, ast.Expr)
                and hasattr(expr, "value")
                and isinstance(expr.value, ast.Constant)
                and isinstance(expr.value.value, str)
            ), f"The {module_type}.{file_name} module should have a docstring at the top"
            module_strings.setdefault(title, {})[file_name] = expr.value.value.strip()

    with open(README_TEMPLATE) as readme_template_file:
        readme_template: Template = Template(readme_template_file.read())

    with open(join(THIS_DIR, "README.md"), "w") as readme_file:
        readme_file.write(
            readme_template.render(dict(repo=True, supported_hardware=module_strings))
        )

    with open(join(DOCS_DIR, "README.md"), "w") as readme_file:
        readme_file.write(
            readme_template.render(dict(repo=False, supported_hardware=module_strings))
        )


def generate_changelog() -> None:
    print("Copying changelog...")
    shutil.copyfile(join(THIS_DIR, "CHANGELOG.md"), join(DOCS_DIR, "CHANGELOG.md"))


def document_gpio_module() -> None:
    # TODO: Tasks pending completion -@flyte at 07/03/2021, 11:19:04
    # Continue writing this to document the modules in some way.
    module = import_module("mqtt_io.modules.gpio.raspberrypi")
    requirements = getattr(module, "REQUIREMENTS", None)
    config_schema = getattr(module, "CONFIG_SCHEMA", None)
    interrupt_support = getattr(module.GPIO, "INTERRUPT_SUPPORT", None)
    pin_schema = getattr(module.GPIO, "PIN_SCHEMA", None)
    input_schema = getattr(module.GPIO, "INPUT_SCHEMA", None)
    output_schema = getattr(module.GPIO, "OUTPUT_SCHEMA", None)


# def get_source(path: str) -> str:
#     module_path, member_path = re.match(r"([\w\.]+):?(.*)", path).groups()
#     module = import_module(module_path)
#     module_filepath = pathlib.Path(module.__file__)
#     url = f"https://github.com/flyte/mqtt-io/blob/develop/{module_filepath.relative_to(THIS_DIR)}"
#     if not member_path:
#         return f"[`{path}`]({url}):\n\n```python\n{inspect.getsource(module)}```"
#     target = module
#     for member in member_path.split("."):
#         target = getattr(target, member)
#     _, lineno = inspect.getsourcelines(target)
#     url += f"#L{lineno}"
#     return f"[`{path}`]({url}):\n\n```python\n{dedent(inspect.getsource(target))}```"


def get_source(module_path: str, xpath: str, title: str) -> str:
    module = import_module(module_path)
    module_filepath = pathlib.Path(module.__file__)
    src, attrib = module_source(module, xpath)[0]
    url = "https://github.com/flyte/mqtt-io/blob/develop/%s#L%s" % (
        module_filepath.relative_to(THIS_DIR),
        attrib["lineno"],
    )
    return f"[{title}]({url}):\n\n```python\n{src.rstrip()}\n```"


def get_source_link(module_path: str, xpath: str, title: str) -> str:
    module = import_module(module_path)
    module_filepath = pathlib.Path(module.__file__)
    _, attrib = module_source(module, xpath)[0]
    url = "https://github.com/flyte/mqtt-io/blob/develop/%s#L%s" % (
        module_filepath.relative_to(THIS_DIR),
        attrib["lineno"],
    )
    return f"[{title}]({url}):"


def get_source_raw(
    module_path: str, xpath: str, until_xpath: Optional[str] = None, dedent: bool = False
) -> str:
    module = import_module(module_path)
    src, _ = module_source(module, xpath, until_xpath=until_xpath, dedent=dedent)[0]
    return src


def get_sources_raw(
    sources_spec: List[Tuple[str, str, Optional[str]]], dedent: bool = False
) -> str:
    src = "\n".join(get_source_raw(*x, dedent=False) for x in sources_spec)
    if dedent:
        src = textwrap.dedent(src)
    return src


def generate_modules_doc() -> None:
    ctx = dict(
        source=get_source,
        source_link=get_source_link,
        source_raw=get_source_raw,
        sources_raw=get_sources_raw,
    )

    with open(MODULES_DOC_TEMPLATE) as modules_doc_template_file:
        modules_doc_template: Template = Template(modules_doc_template_file.read())

    with open(join(DOCS_DIR, "dev/modules/README.md"), "w") as readme_file:
        readme_file.write(modules_doc_template.render(ctx))


def main() -> None:
    print(f"Loading YAML config schema from '{CONFIG_SCHEMA_PATH}'...")
    with open(CONFIG_SCHEMA_PATH, "r") as config_schema_file:
        config_schema: ConfigType = yaml.safe_load(config_schema_file)

    print(f"Loading sidebar template from '{SIDEBAR_TEMPLATE}'...")
    with open(SIDEBAR_TEMPLATE, "r") as sidebar_template_file:
        sidebar_template: Template = Template(sidebar_template_file.read())

    print(f"Loading content template from '{CONTENT_TEMPLATE}'...")
    with open(CONTENT_TEMPLATE, "r") as content_template_file:
        content_template: Template = Template(content_template_file.read())

    top_level_section_names: List[str] = list(config_schema.keys())
    ConfigSchemaParser.parse_schema_section(config_schema, [])

    main_sidebar_path = join(DOCS_DIR, "_sidebar.md")
    print(f"Writing main sidebar file '{main_sidebar_path}'...")
    with open(main_sidebar_path, "w") as main_sidebar_file:
        main_sidebar_file.write(
            sidebar_template.render(
                dict(ref_sections=[x for x in REF_ENTRIES if x["depth"] == 0])
            )
        )

    for tl_section in top_level_section_names:
        section_path = join(DOCS_DIR, f"config/reference/{tl_section}")
        md_path = join(section_path, "README.md")

        print(f"Making directory (if not exists) '{section_path}'...")
        os.makedirs(section_path, exist_ok=True)

        print(f"Making section markdown file '{md_path}'...")
        with open(md_path, "w") as md_file:
            md_file.write(
                content_template.render(
                    dict(ref_sections=REF_ENTRIES, section=tl_section)
                )
            )

    json_schema_path = join(DOCS_DIR, "schema.json")
    print(f"Making JSON config schema file '{json_schema_path}'...")
    with open(json_schema_path, "w") as json_schema_file:
        json.dump(config_schema, json_schema_file, indent=2)

    # generate_module_docs()
    generate_readmes()
    generate_changelog()
    generate_modules_doc()


if __name__ == "__main__":
    main()
