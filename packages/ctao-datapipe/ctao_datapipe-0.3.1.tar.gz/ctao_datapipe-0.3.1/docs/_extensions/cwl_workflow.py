#!/usr/bin/env python3
"""Sphinx directives to document a CWL workflows."""

import hashlib
import os
import re
import subprocess
from pathlib import Path

import yaml
from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList
from sphinx.util.logging import getLogger
from sphinx.util.nodes import nested_parse_with_titles

logger = getLogger(__name__)

GRAPH_DIR = "_static"


def parse_rst(text, directive):
    """Parse RST string into nodes using Sphinx's parser."""
    result = ViewList()
    for line in text.splitlines():
        result.append(line, "<cwl-doc>")
    node = nodes.container()
    nested_parse_with_titles(directive.state, result, node)
    return node.children


class CWLWorkflowGraphDirective(Directive):
    """CWL Workflow Graph Directive."""

    has_content = False
    required_arguments = 1  # path to the CWL file

    def run(self):
        """Generate sphinx."""
        env = self.state.document.settings.env
        app = env.app

        cwl_rel_path = self.arguments[0]
        cwl_abs_path = os.path.abspath(os.path.join(env.srcdir, cwl_rel_path))

        if not os.path.isfile(cwl_abs_path):
            error = self.state_machine.reporter.error(
                f"CWL file not found: {cwl_rel_path}", line=self.lineno
            )
            return [error]

        # Unique output name based on file path
        hash_id = hashlib.sha256(cwl_rel_path.encode("utf-8")).hexdigest()[:10]
        base_name = os.path.splitext(os.path.basename(cwl_rel_path))[0]
        svg_filename = f"{base_name}-{hash_id}.svg"

        # Output directory for graphs
        graph_dir = os.path.join(app.srcdir, GRAPH_DIR, "cwl-graphs")
        os.makedirs(graph_dir, exist_ok=True)
        svg_path = os.path.join(graph_dir, svg_filename)

        # Run cwltool | dot -Tsvg
        try:
            logger.info(
                "[CWLGraph] Generating SVG for } %s -> %s", cwl_rel_path, svg_path
            )
            cwl_proc = subprocess.Popen(
                ["cwltool", "--print-dot", cwl_abs_path],
                stdout=subprocess.PIPE,
            )
            subprocess.run(
                ["dot", "-Tsvg", "-o", svg_path],
                stdin=cwl_proc.stdout,
                check=True,
            )
            cwl_proc.stdout.close()
            cwl_proc.wait()
        except subprocess.CalledProcessError as e:
            error = self.state_machine.reporter.error(
                f"Error generating workflow graph: {e}", line=self.lineno
            )
            return [error]

        # Embed the resulting SVG
        rel_svg_uri = os.path.join(GRAPH_DIR, "cwl-graphs", svg_filename)
        return [nodes.image(uri=rel_svg_uri)]


def slugify(text):
    """Normalize a name to work as a sphinx ID."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class CWLWorkflowDirective(Directive):
    """CWL Workflow Directive."""

    has_content = False
    required_arguments = 1  # path to the CWL file

    def run(self):
        """Generate sphinx."""
        env = self.state.document.settings.env
        cwl_rel_path = Path(self.arguments[0])
        cwl_abs_path = os.path.abspath(os.path.join(env.srcdir, cwl_rel_path))
        cwl_workflow_name = cwl_rel_path.name

        if not os.path.isfile(cwl_abs_path):
            error = self.state_machine.reporter.error(
                f"CWL file not found: {cwl_rel_path}", line=self.lineno
            )
            return [error]

        try:
            # Parse the whole CWL content here
            with open(cwl_abs_path) as f:
                content = yaml.safe_load(f)

            label = content.get("label", cwl_workflow_name.replace(".cwl", ""))
            doc = content.get("doc", None)
            inputs = content.get("inputs", {})
            outputs = content.get("outputs", {})
            cwl_class = content.get("class", "?")

            if isinstance(inputs, list):
                inputs = {item["id"]: item for item in inputs}
            if isinstance(outputs, list):
                outputs = {item["id"]: item for item in outputs}

        except Exception as e:
            error = self.state_machine.reporter.error(
                f"Failed to parse CWL file: {e}", line=self.lineno
            )
            return [error]

        # Create the document node
        section = nodes.section()
        section["ids"].append(slugify(cwl_workflow_name))

        section += nodes.title(text=label)
        info = nodes.paragraph()
        info += nodes.strong(text=cwl_class + ": ")
        info += nodes.Text(cwl_workflow_name)

        section += info
        section += parse_rst(doc, self)

        section += nodes.strong(text="Inputs:")
        section += self.make_table(inputs)

        section += nodes.strong(text="Outputs:")
        section += self.make_table(outputs)

        return [section]

    def make_table(self, io_dict):
        """Make table of inputs/outputs."""
        table = nodes.table()
        tgroup = nodes.tgroup(cols=3)
        table += tgroup

        for _ in range(3):
            tgroup += nodes.colspec(colwidth=1)

        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for label in ["ID", "Type", "Description"]:
            entry = nodes.entry()
            entry += nodes.paragraph(text=label)
            header_row += entry
        thead += header_row

        tbody = nodes.tbody()
        tgroup += tbody

        for key, val in io_dict.items():
            row = nodes.row()

            # ID
            id_entry = nodes.entry()
            id_entry += nodes.literal(text=key)
            row += id_entry

            # Type
            type_text = val.get("type", "Unknown")
            if isinstance(type_text, list):
                type_text = " | ".join(str(t) for t in type_text)
            type_entry = nodes.entry()
            type_entry += nodes.literal(text=str(type_text))
            row += type_entry

            # Description
            desc = val.get("doc", "")
            desc_entry = nodes.entry()
            desc_entry += parse_rst(desc, self)
            row += desc_entry

            tbody += row

        return table


def setup(app):
    """Create Sphinx App."""
    app.add_directive("cwl_workflow_graph", CWLWorkflowGraphDirective)
    app.add_directive("cwl_workflow", CWLWorkflowDirective)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
