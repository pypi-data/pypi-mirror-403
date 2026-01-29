from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from glyph.core.workspace import Workspace
from glyph.core.utils.docx_intake import intake_docx
from glyph.core.schema.build_schema import GlyphSchemaBuilder
from glyph.core.schema_runner.run_schema import GlyphSchemaRunner



def build_schema(document_xml_path: str, extract_dir: str | None = None, source_docx: str | None = None, tag: str | None = None) -> dict:
    """
    Build a glyph schema from a document.xml and (optionally) its extracted DOCX folder.
    """
    builder = GlyphSchemaBuilder(
        document_xml_path=document_xml_path,
        docx_extract_dir=extract_dir,
        source_docx=source_docx,
        tag=tag,
    )
    return builder.run()


def main():
    parser = argparse.ArgumentParser(prog="glyph", description="glyph SDK CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- schema subcommand ---
    sch = sub.add_parser("schema", help="Generate JSON schema from a .docx")
    sch.add_argument("--in", dest="docx", required=True, help="Path to input .docx")
    sch.add_argument("--out", dest="out", help="Optional path to write schema.json")
    sch.add_argument("--workspace", dest="wsroot", help="Optional workspace root (default: .glyph or glyph_workspace)")

    # --- run subcommand ---
    runp = sub.add_parser("run", help="Generate a DOCX from an existing schema.json")
    runp.add_argument("--schema", dest="schema", required=True, help="Path to schema.json")
    runp.add_argument("--out", dest="out", help="Path to save generated .docx")
    runp.add_argument("--source", dest="source", help="Optional override for source .docx")

    args = parser.parse_args()

    if args.cmd in ("schema", "configs"):
        ws = Workspace(root_dir=args.wsroot) if args.wsroot else Workspace()

        # Use workspace tagged operations for consistent tagging
        schema, ws_schema_path = ws.tagged_intake_and_build_schema(
            src_docx=args.docx,
        )

        if args.out:
            out_path = Path(args.out)
            # Add tag to output file if workspace has one
            if ws.tag:
                name = out_path.stem
                suffix = out_path.suffix
                tagged_out_path = out_path.parent / f"{name}_{ws.tag}{suffix}"
            else:
                tagged_out_path = out_path
            
            tagged_out_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
            print(f"Schema saved: {ws_schema_path} (mirrored to {tagged_out_path})")
            if ws.tag:
                print(f"Tag used: {ws.tag}")
        else:
            print(json.dumps(schema, indent=2))
            print(f"\n[Workspace copy saved at {ws_schema_path}]")
            if ws.tag:
                print(f"Tag used: {ws.tag}")

    elif args.cmd == "run":
        # Load schema and check for tag
        schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
        
        if args.source:
            schema["source_docx"] = args.source
        
        if args.out:
            # Use workspace for tagged run
            ws = Workspace()
            actual_output_path = ws.tagged_run_schema(
                schema=schema,
                output_path=args.out,
            )
            print(f"[glyph] DOCX written to {actual_output_path}")
            if schema.get("tag"):
                print(f"Tag used: {schema['tag']}")
        else:
            run_schema(
                schema_path=args.schema,
                output_path=args.out,
                source_override=args.source,
            )


def run_schema(schema_path: str, output_path: str | None = None, source_override: str | None = None) -> None:
    """
    Run an existing schema JSON through GlyphSchemaRunner to generate a DOCX.

    :param schema_path: Path to schema.json
    :param output_path: Optional output DOCX path
    :param source_override: Optional override for schema["source_docx"]
    """
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))

    if source_override:
        schema["source_docx"] = source_override

    if "source_docx" not in schema:
        raise ValueError("Schema missing 'source_docx'. Provide one via schema or source_override.")

    runner = GlyphSchemaRunner(schema)
    results = runner.run()

    if output_path:
        runner.document.save(output_path)
        print(f"[glyph] DOCX written to {output_path}")
    else:
        # Default: print debug trace of results
        json.dump(
            [{"text": t, "type": d.get("type"), "style": s} for t, d, s in results],
            sys.stdout,
            indent=2,
        )

if __name__ == "__main__":
    main()
