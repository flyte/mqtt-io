# pylint: disable-all

import os.path
from argparse import ArgumentParser
from shutil import move
from textwrap import dedent, indent
from typing import Any, Callable, List, Optional, TextIO

import md_toc  # type: ignore
import yaml

from ..types import ConfigType
from . import get_main_schema


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


class SectionDocumenter:
    def __init__(self, doc: Callable[[str], None]):
        self.doc = doc

    def document_schema_section(
        self, schema_section: ConfigType, parent_sections: Optional[List[str]] = None
    ) -> None:
        if parent_sections is None:
            parent_sections = []
        else:
            parent_sections = parent_sections.copy()

        child_schema = schema_section.get("schema")
        if child_schema:
            # This must be a list, which has a schema for each item
            parent_sections.append("*")
            self.document_schema_section(child_schema, parent_sections)
            return
        for entry_name in schema_section.keys():
            entry: ConfigType = schema_section[entry_name]
            self.document_cerberus_section(entry_name, entry, parent_sections)

    def document_cerberus_section(
        self, entry_name: str, cerberus_section: ConfigType, parent_sections: List[str]
    ) -> None:
        parent_sections = parent_sections.copy()

        auto_title = ""
        if parent_sections:
            # auto_title += "_" + ".".join(parent_sections) + "_."
            auto_title += ".".join(parent_sections) + "."
        auto_title += f"`{entry_name}`"

        title = meta_entry(cerberus_section, "title") or auto_title

        child_schema = cerberus_section.get("schema")

        depth = len([x for x in parent_sections if x != "*"])
        dashes = "- " * depth
        hashes = "#" * (depth + 1)
        if child_schema and not entry_name.endswith("*"):
            self.doc(f"\n\n{hashes} {title}")
        else:
            self.doc(f"\n\n{dashes}{hashes} {title}")

        self.doc("\n\n```yaml")

        type_str: str = format_yaml_value(cerberus_section["type"])
        self.doc(f"\nType:{type_str}")

        required: bool = cerberus_section.get("required", False)
        self.doc("\nRequired: %s" % ("yes" if required else "no"))

        unit = meta_entry(cerberus_section, "unit")
        if unit is not None:
            self.doc(f"\nUnit: {unit}")

        allowed = cerberus_section.get("allowed")
        if allowed is not None:
            allowed_str: str = yaml.dump(allowed)
            self.doc(f"\nAllowed:\n{allowed_str.strip()}")

        min_val = cerberus_section.get("min")
        if min_val is not None:
            self.doc(f"\nMinimum value: {min_val}")

        max_val = cerberus_section.get("max")
        if max_val is not None:
            self.doc(f"\nMinimum value: {max_val}")

        allow_unknown = cerberus_section.get("allow_unknown")
        if allow_unknown is not None:
            allow_unknown_str = "yes" if allow_unknown else "no"
            self.doc(f"\nUnlisted entries accepted: {allow_unknown_str}")

        if "default" in cerberus_section:
            default_str = format_yaml_value(cerberus_section["default"])
            self.doc(f"\nDefault:{default_str}")

        self.doc("\n```")

        description = meta_entry(cerberus_section, "description")
        if description:
            self.doc(f"\n\n{description}")

        extra_info = meta_entry(cerberus_section, "extra_info")
        if extra_info:
            self.doc(f"\n\n> {extra_info}")

        yaml_example = meta_entry(cerberus_section, "yaml_example")
        if yaml_example:
            self.doc(f"\n\n**Example:**\n\n```yaml\n{yaml_example}\n```")

        yaml_example_expand = meta_entry(cerberus_section, "yaml_example_expand")
        if yaml_example_expand:
            self.doc(
                dedent(
                    f"""\n
                    <details>
                    <summary>View example</summary>

                    ```yaml
                    {yaml_example_expand}
                    ```
                    </details>
                    """
                ).rstrip("\n")
            )

        if child_schema:
            parent_sections.append(entry_name)
            if "type" in child_schema:
                self.document_cerberus_section("*", child_schema, parent_sections)
            else:
                self.document_schema_section(child_schema, parent_sections)


def document_schema(doc_file: TextIO) -> None:
    schema = get_main_schema()

    def doc(entry: str) -> None:
        print(entry, file=doc_file, end="")

    doc(
        dedent(
            """
            The software is configured using a single YAML config file. This document details
            the config options for each section and provides examples.

            <!-- TOC -->
            """
        ).strip()
    )

    sd = SectionDocumenter(doc)
    sd.document_schema_section(schema)


def add_toc(path: str) -> None:
    toc = md_toc.build_toc(path, keep_header_levels=10, skip_lines=1)
    md_toc.write_string_on_file_between_markers(path, toc, "<!-- TOC -->")


def main() -> None:
    p = ArgumentParser()
    p.add_argument("output_path")
    args = p.parse_args()
    path, fname = os.path.split(args.output_path)
    tmp_path = os.path.join(path, f"~{fname}")
    with open(tmp_path, "w") as _doc_file:
        document_schema(_doc_file)
    add_toc(tmp_path)
    move(tmp_path, args.output_path)


if __name__ == "__main__":
    main()
