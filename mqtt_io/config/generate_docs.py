from shutil import move
from textwrap import dedent
from typing import Any, Callable, List, Optional, TextIO

import md_toc
import yaml

from ..types import ConfigType
from . import get_main_schema

DOC_PATH = "config-doc.md"


def meta_entry(section: ConfigType, meta_key: str) -> Any:
    entry = section.get("meta", {}).get(meta_key, "")
    if hasattr(entry, "strip"):
        entry = entry.strip()
    return entry or None


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
        self.doc(f"\n<!--cerberus_section(depth={len(parent_sections)})-->")

        auto_title = ""
        if parent_sections:
            auto_title += "<small>_" + ".".join(parent_sections) + "_.</small>"
        auto_title += f"`{entry_name}`"

        title = meta_entry(cerberus_section, "title") or auto_title

        child_schema = cerberus_section.get("schema")

        depth = len([x for x in parent_sections if x != "*"])
        dashes = "- " * depth
        hashes = "#" * (depth + 1)
        if child_schema:
            self.doc(f"\n\n{hashes} {title}")
        else:
            self.doc(f"\n\n{dashes}{hashes} {title}")

        # if child_schema:
        #     self.doc("\n\n-------------------")

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

        if yaml_example := meta_entry(cerberus_section, "yaml_example"):
            self.doc(f"\n\n**Example:**\n\n```yaml\n{yaml_example}\n```")

        if yaml_example_expand := meta_entry(cerberus_section, "yaml_example_expand"):
            self.doc(
                f"""\n
<details>
  <summary>View example</summary>

```yaml
{yaml_example_expand}
```
</details>"""
            )

        if child_schema:
            # self.doc(f"\n\n{hashes}# `{entry_name}` config")
            parent_sections.append(entry_name)
            self.document_schema_section(child_schema, parent_sections)
            return


def document_schema(doc_file: TextIO) -> None:
    schema = get_main_schema()

    def doc(entry: str) -> None:
        print(entry, file=doc_file, end="")

    doc(
        dedent(
            """
        # MQTT IO Configuration

        The software is configured using a single YAML config file. This document details
        the config options for each section and provides examples for each section.

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
    tmp_path = f"~{DOC_PATH}"
    with open(tmp_path, "w") as _doc_file:
        document_schema(_doc_file)
    add_toc(tmp_path)
    move(tmp_path, DOC_PATH)


if __name__ == "__main__":
    main()
