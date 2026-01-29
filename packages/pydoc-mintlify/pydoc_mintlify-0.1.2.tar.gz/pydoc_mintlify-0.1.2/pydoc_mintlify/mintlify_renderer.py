# -*- coding: utf8 -*-

import dataclasses
import json
import logging
import os
import typing as t
from pathlib import Path

import docspec
import typing_extensions as te
import yaml
from databind.core import DeserializeAs
from pydoc_markdown.contrib.renderers.markdown import MarkdownRenderer
from pydoc_markdown.interfaces import Context, Renderer

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class CustomizedMarkdownRenderer(MarkdownRenderer):
    """We override some defaults in this subclass."""

    #: Disabled because Docusaurus supports this automatically.
    insert_header_anchors: bool = False

    #: Escape html in docstring, otherwise it could lead to invalid html.
    escape_html_in_docstring: bool = False

    #: Conforms to Docusaurus header format.
    render_module_header_template: str = (
        "---\nsidebar_label: {relative_module_name}\ntitle: {module_name}\n---\n\n"
    )


@dataclasses.dataclass
class MintlifyRenderer(Renderer):
    """Render Markdown and update Mintlify docs.json tab.

    Accepts only:
      - markdown: Markdown renderer configuration
      - docs_base_path: Root docs directory (default: 'docs')
      - nav: Dict representing a Mintlify navigation tab to insert/replace
    """

    #: The #MarkdownRenderer configuration.
    markdown: te.Annotated[
        MarkdownRenderer, DeserializeAs(CustomizedMarkdownRenderer)
    ] = dataclasses.field(default_factory=CustomizedMarkdownRenderer)

    #: The path where the Mintlify docs content is. Defaults to "docs" folder.
    docs_base_path: str = "docs"

    #: The navigation tab to insert/replace in docs.json.
    nav: t.Dict[str, t.Any] = dataclasses.field(default_factory=dict)

    def init(self, context: Context) -> None:
        """Initialize the underlying Markdown renderer.

        Args:
            context: Pydoc-Markdown context.
        """
        self.markdown.init(context)
        self.pages = _collect_pages(self.nav)

    def render(self, modules: t.List[docspec.Module]) -> None:
        """Render modules to MDX into a tab folder and update docs.json tab.

        Args:
            modules: The list of modules to render.
        """
        # Determine tab folder
        try:
            tab_name = t.cast(str, self.nav["tab"])
        except KeyError as exc:
            raise KeyError("nav must include a 'tab' string") from exc
        normalized_tab = self._normalize_tab_name(tab_name)
        output_root = Path(self.docs_base_path) / normalized_tab

        # Disable default module header to avoid duplicated frontmatter.
        self.markdown.render_module_header = False

        module_tree: t.Dict[str, t.Any] = {"children": {}, "edges": []}

        for module in modules:
            filepath = output_root

            module_parts = module.name.split(".")
            if module.location.filename.endswith("__init__.py"):
                module_parts.append("__init__")

            relative_module_tree = module_tree
            intermediary_module = []

            for module_part in module_parts[:-1]:
                # update the module tree
                intermediary_module.append(module_part)
                intermediary_module_name = ".".join(intermediary_module)
                relative_module_tree["children"].setdefault(
                    intermediary_module_name, {"children": {}, "edges": []}
                )
                relative_module_tree = relative_module_tree["children"][
                    intermediary_module_name
                ]

                # descend to the file
                filepath = filepath / module_part

            # create intermediary missing directories and get the full path
            filepath.mkdir(parents=True, exist_ok=True)
            filepath = filepath / f"{module_parts[-1]}.mdx"

            mintlify_path = str(filepath.relative_to(output_root).with_suffix(""))

            with filepath.open("w", encoding=self.markdown.encoding) as fp:
                logger.info("Render file %s", filepath)
                # Minimal frontmatter
                frontmatter: t.Dict[str, t.Any] = self.pages.get(mintlify_path, {})
                frontmatter.pop("path", None)

                # Write YAML frontmatter header.
                fp.write("---\n")
                fp.write(yaml.safe_dump(frontmatter, sort_keys=False))
                fp.write("---\n\n")

                # Render the API content below the frontmatter.
                self.markdown.render_single_page(fp, [module])
            # only update the relative module tree if the file is not empty
            relative_module_tree["edges"].append(
                os.path.splitext(str(filepath.relative_to(self.docs_base_path)))[0]
            )

        # Update docs.json tab
        updated_tab = self._prefix_nav_pages(
            self.nav, self.docs_base_path, normalized_tab
        )
        self._update_docs_tab(Path(self.docs_base_path) / "docs.json", updated_tab)

    @staticmethod
    def _normalize_tab_name(name: str) -> str:
        return name.lower().replace(" ", "_")

    @staticmethod
    def _prefix_nav_pages(
        tab_obj: t.Dict[str, t.Any], docs_base_path: str, normalized_tab: str
    ) -> t.Dict[str, t.Any]:
        """Return a copy of the tab object with each page path prefixed by
        '<normalized_tab>/' recursively through groups/pages.
        Avoid double-prefixing if already present.
        """
        prefix = normalized_tab

        def transform_entries(
            entries: t.Iterable[t.Union[str, t.Dict[str, t.Any]]],
        ) -> t.List[t.Union[str, t.Dict[str, t.Any]]]:
            out: t.List[t.Union[str, t.Dict[str, t.Any]]] = []
            for entry in entries:
                if isinstance(entry, str):
                    page = entry.lstrip("/")
                    if page == normalized_tab or page.startswith(f"{normalized_tab}/"):
                        out.append(page)
                    else:
                        out.append(f"{prefix}/{page}")
                elif isinstance(entry, dict):
                    # Two forms: page dict with 'path', or group dict with 'pages'
                    if "pages" in entry and isinstance(entry.get("pages"), list):
                        group_label = entry.get("group")
                        child_pages = entry.get("pages")
                        out.append(
                            {
                                "group": group_label,
                                "pages": transform_entries(
                                    t.cast(
                                        t.List[t.Union[str, t.Dict[str, t.Any]]],
                                        child_pages,
                                    )
                                ),
                            }
                        )
                    elif "path" in entry and isinstance(entry.get("path"), str):
                        page_path = t.cast(str, entry.get("path", "")).lstrip("/")
                        if page_path == normalized_tab or page_path.startswith(
                            f"{normalized_tab}/"
                        ):
                            out.append(page_path)
                        else:
                            out.append(f"{prefix}/{page_path}")
                    else:
                        out.append(entry)
                else:
                    out.append(entry)
            return out

        new_tab: t.Dict[str, t.Any] = {
            k: v for k, v in tab_obj.items() if k not in ("pages", "groups")
        }
        if isinstance(tab_obj.get("pages"), list):
            new_tab["pages"] = transform_entries(tab_obj["pages"])  # type: ignore[index]
        if isinstance(tab_obj.get("groups"), list):
            groups_out: t.List[t.Dict[str, t.Any]] = []
            for group in tab_obj["groups"]:  # type: ignore[index]
                if isinstance(group, dict):
                    group_label = group.get("group")
                    pages = group.get("pages", [])
                    if isinstance(pages, list):
                        groups_out.append(
                            {
                                "group": group_label,
                                "pages": transform_entries(pages),
                            }
                        )
                    else:
                        groups_out.append(group)
                else:
                    # Non-dict group entry; pass through
                    groups_out.append(group)  # type: ignore[arg-type]
            new_tab["groups"] = groups_out
        return new_tab

    @staticmethod
    def _update_docs_tab(docs_path: Path, tab_obj: t.Dict[str, t.Any]) -> None:
        """Replace or append the given tab in docs.json, preserving other content.
        If docs.json does not exist, create a minimal structure with this tab only.
        """
        if not docs_path.exists():
            content: t.Dict[str, t.Any] = {"navigation": {"tabs": [tab_obj]}}
        else:
            with docs_path.open("r", encoding="utf-8") as f:
                try:
                    content = json.load(f)
                except json.JSONDecodeError:
                    # If file exists but invalid, reset to minimal valid structure
                    content = {}
            nav = content.setdefault("navigation", {})
            tabs = nav.setdefault("tabs", [])
            tab_name = tab_obj.get("tab")
            replaced = False
            for idx, existing in enumerate(tabs):
                if isinstance(existing, dict) and existing.get("tab") == tab_name:
                    tabs[idx] = tab_obj
                    replaced = True
                    break
            if not replaced:
                tabs.append(tab_obj)
        with docs_path.open("w", encoding="utf-8") as f:
            logger.info("Render file %s", docs_path)
            json.dump(content, f, indent=2, sort_keys=False)


def _collect_pages(nav: str | t.Dict[str, t.Any]) -> t.List[dict]:
    result = {}
    match nav:
        case str():
            result[nav] = {"path": nav}
        case {"pages": pages}:
            for page in pages:
                result |= _collect_pages(page)
        case {"groups": groups}:
            for group in groups:
                result |= _collect_pages(group)
        case {"path": path} as page:
            result[path] = page.copy()
        case _:
            raise ValueError(f"Invalid page entry: {nav}")
    return result
