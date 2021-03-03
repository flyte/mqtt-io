from textwrap import dedent, indent
from typing import Any, List, Optional

import yaml
from docutils import nodes
from docutils.parsers.rst import Directive
from mqtt_io.config import get_main_schema
from mqtt_io.types import ConfigType
from recommonmark.parser import CommonMarkParser
from sphinx.directives.code import CodeBlock
from sphinx.util.docutils import SphinxDirective


def meta_entry(section: ConfigType, meta_key: str) -> Any:
    entry = section.get("meta", {}).get(meta_key, "")
    if hasattr(entry, "strip"):
        entry = entry.strip()
    return entry or None


def titleify(text: str) -> str:
    return text.replace("_", " ").title()


def format_yaml_value(value: Any) -> str:
    value_str: str = yaml.dump(value, default_style=None)
    if value_str.endswith("\n...\n"):
        value_str = " " + value_str[: -len("\n...\n")]
    elif "\n" not in value_str.rstrip("\n"):
        value_str = " " + value_str.rstrip("\n")
    else:
        value_str = "\n" + indent(value_str.rstrip("\n"), "  ")
    return value_str


def add_title(
    section: nodes.section,
    entry_name: str,
    parent_sections: List[str],
) -> None:
    title = nodes.title()
    title_str: str = ""
    if parent_sections:
        parent_sections_em = nodes.emphasis()
        title_str += ".".join(parent_sections) + "."
        parent_sections_em += nodes.Text(title_str)
        title += parent_sections_em
    title_strong = nodes.strong()
    title_strong += nodes.Text(entry_name)
    title += title_strong
    title_str += entry_name
    section["ids"] = [title_str]
    section += title


def add_yaml_details(parent: nodes.Element, section: ConfigType) -> None:
    lines = []

    type_str: str = format_yaml_value(section["type"])
    lines.append(f"Type:{type_str}")

    required: bool = section.get("required", False)
    lines.append("Required: %s" % ("yes" if required else "no"))

    unit = meta_entry(section, "unit")
    if unit is not None:
        lines.append(f"Unit: {unit}")

    allowed = section.get("allowed")
    if allowed is not None:
        allowed_str: str = yaml.dump(allowed)
        lines.append(f"Allowed:\n{allowed_str.strip()}")

    min_val = section.get("min")
    if min_val is not None:
        lines.append(f"Minimum value: {min_val}")

    max_val = section.get("max")
    if max_val is not None:
        lines.append(f"Minimum value: {max_val}")

    allow_unknown = section.get("allow_unknown")
    if allow_unknown is not None:
        allow_unknown_str = "yes" if allow_unknown else "no"
        lines.append(f"Unlisted entries accepted: {allow_unknown_str}")

    if "default" in section:
        default_str = format_yaml_value(section["default"])
        lines.append(f"Default:{default_str}")

    details_str = "\n".join(lines)
    literal = nodes.literal_block(details_str, details_str)
    literal["language"] = "yaml"
    parent.append(literal)


def add_description(
    parent: nodes.Element, section: ConfigType, document: nodes.document
) -> None:
    description = meta_entry(section, "description")
    if not description:
        return
    tmp_doc = nodes.document(document.settings, document.reporter)
    cmp = CommonMarkParser()
    cmp.parse(description, tmp_doc)
    parent += tmp_doc.children


def add_extra_info(
    parent: nodes.Element, section: ConfigType, document: nodes.document
) -> None:
    extra_info = meta_entry(section, "extra_info")
    if not extra_info:
        return
    note = nodes.note()
    tmp_doc = nodes.document(document.settings, document.reporter)
    cmp = CommonMarkParser()
    cmp.parse(extra_info, tmp_doc)
    note += tmp_doc.children
    parent += note


def add_yaml_example(parent: nodes.Element, section: ConfigType) -> None:
    yaml_example = meta_entry(section, "yaml_example")
    if not yaml_example:
        return
    para = nodes.paragraph()
    strong = nodes.strong()
    strong += nodes.Text("Example:")
    para += strong
    literal = nodes.literal_block(yaml_example, yaml_example)
    literal["language"] = "yaml"
    para += literal
    parent += para


class ConfigSchemaDirective(SphinxDirective):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._nodes: List[Any] = []

    def document_schema_section(
        self,
        schema_section: ConfigType,
        parent_sections: Optional[List[str]] = None,
        parent_container: Optional[nodes.container] = None,
    ) -> nodes.container:
        if parent_sections is None:
            parent_sections = []
        else:
            parent_sections = parent_sections.copy()

        child_schema = schema_section.get("schema")
        if child_schema:
            # This must be a list, which has a schema for each item
            parent_sections.append("*")
            self.document_schema_section(child_schema, parent_sections, parent_container)
            return parent_container

        depth = len([x for x in parent_sections if x != "*"])
        container = nodes.container()
        container.set_class(f"schema-{depth}")

        if parent_container is not None:
            parent_container.append(container)

        for entry_name in schema_section.keys():
            entry: ConfigType = schema_section[entry_name]
            self.document_cerberus_section(entry_name, entry, parent_sections, container)

        return container

    def document_cerberus_section(
        self,
        entry_name: str,
        cerberus_section: ConfigType,
        parent_sections: List[str],
        container: nodes.container,
    ) -> None:
        parent_sections = parent_sections.copy()
        child_schema = cerberus_section.get("schema")

        section = nodes.section()
        add_title(section, entry_name, parent_sections)
        add_yaml_details(section, cerberus_section)
        add_description(section, cerberus_section, self.state.document)
        add_extra_info(section, cerberus_section, self.state.document)
        add_yaml_example(section, cerberus_section)

        container += section

        if child_schema:
            parent_sections.append(entry_name)
            if "type" in child_schema:
                self.document_cerberus_section(
                    "*", child_schema, parent_sections, container
                )
            else:
                self.document_schema_section(child_schema, parent_sections, container)

    def run(self):
        return [self.document_schema_section(get_main_schema())]


def setup(app):
    app.add_directive("configschema", ConfigSchemaDirective)
    return dict(version="0.0.1")
