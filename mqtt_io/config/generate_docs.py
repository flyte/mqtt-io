from shutil import move
from textwrap import dedent
import textwrap
from types import FunctionType
from typing import Any, Callable, List, Optional, TextIO, cast

import yaml

from ..types import ConfigType
from . import get_main_schema

DOC_PATH = "config-doc.md"


def meta_entry(section: ConfigType, meta_key: str) -> Any:
    return section.get("meta", {}).get(meta_key, "").strip() or None


def titleify(text: str) -> str:
    return text.replace("_", " ").title()


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
        self.doc(f"\n<!--schema_section(depth={len(parent_sections)})-->")
        if child_schema := schema_section.get("schema"):
            self.document_schema_section(child_schema, parent_sections)
            return
        for entry_name in schema_section.keys():
            entry: ConfigType = schema_section[entry_name]
            self.document_cerberus_section(entry_name, entry, parent_sections)

    def document_cerberus_section(
        self, entry_name: str, cerberus_section: ConfigType, parent_sections: List[str]
    ) -> None:
        parent_sections = parent_sections.copy()
        self.doc(f"\n<!--cerberus_section(depth={len(parent_sections)})-->")

        auto_title = ""
        if parent_sections:
            auto_title += "<small>_" + ".".join(parent_sections) + "_.</small>"
        auto_title += f"`{entry_name}`"

        title = meta_entry(cerberus_section, "title") or auto_title

        dashes = "- " * (len(parent_sections))
        hashes = "#" * (len(parent_sections) + 2)
        self.doc(f"\n\n{dashes}{hashes} {title}")

        # dashes = "- " * (len(parent_sections))
        # self.doc(f"\n\n{dashes}**{title}**:")

        if child_schema := cerberus_section.get("schema"):
            self.doc("\n\n-------------------")

        self.doc("\n\n```yaml")

        type_str: str = cerberus_section["type"]
        self.doc(f"\nType: {type_str}")

        required: bool = cerberus_section.get("required", False)
        self.doc("\nRequired: %s" % ("yes" if required else "no"))

        if default := cerberus_section.get("default"):
            default_str: str = yaml.dump(default, default_style=None)
            if default_str.endswith("\n...\n"):
                default_str = " " + default_str[: -len("\n...\n")]
            elif "\n" not in default_str.rstrip("\n"):
                default_str = " " + default_str.rstrip("\n")
            else:
                default_str = "\n" + default_str.rstrip("\n")
            self.doc(f"\nDefault:{default_str}")

        if unit := meta_entry(cerberus_section, "unit"):
            self.doc(f"\nUnit: {unit}")

        if allowed := cerberus_section.get("allowed"):
            allowed_str: str = yaml.dump(allowed)
            self.doc(f"\nAllowed:\n{allowed_str.strip()}")

        if min_val := cerberus_section.get("min"):
            self.doc(f"\nMinimum value: {min_val}")

        if max_val := cerberus_section.get("max"):
            self.doc(f"\nMinimum value: {max_val}")

        self.doc("\n```")

        if description := meta_entry(cerberus_section, "description"):
            self.doc(f"\n\n{description}")

        if extra_info := meta_entry(cerberus_section, "extra_info"):
            self.doc(f"\n\n> {extra_info}")

        if child_schema:
            # self.doc("\n\n### Section options:")
            parent_sections.append(entry_name)
            self.document_schema_section(child_schema, parent_sections)
            return


def main(doc_file: TextIO) -> None:
    schema = get_main_schema()

    def doc(entry: str) -> None:
        print(entry, file=doc_file, end="")

    doc(
        dedent(
            """
        # MQTT IO Configuration

        Description stuff...
"""
        ).strip()
    )

    sd = SectionDocumenter(doc)
    sd.document_schema_section(schema)

    # for section_name in schema.keys():
    #     section: ConfigType = schema[section_name]

    # title = meta_entry(section, "title") or titleify(section_name)
    # doc(f"\n\n## {title}")

    # required: bool = section["required"]
    # doc("\n\n")
    # doc("_Required section_" if required else "_Optional section_")

    # if description := meta_entry(section, "description"):
    #     doc(f"\n\n{description}")

    #     section_schema: ConfigType = {}
    #     if section["type"] == "dict":
    #         section_schema = section.get("schema", {})
    #     elif section["type"] == "list":
    #         section_schema = section.get("schema", {}).get("schema", {})
    #     for entry_name in section_schema.keys():
    #         entry: ConfigType = section_schema[entry_name]
    #         doc(f"\n\n### {entry_name}")
    #         required: bool = entry["required"]
    #         doc(f"\n\n")
    #         doc("_Required_" if required else "_Optional_")


if __name__ == "__main__":
    with open(f"~{DOC_PATH}", "w") as _doc_file:
        main(_doc_file)
    move(f"~{DOC_PATH}", DOC_PATH)
