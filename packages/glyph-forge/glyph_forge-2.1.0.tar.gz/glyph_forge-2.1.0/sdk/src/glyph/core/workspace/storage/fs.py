# glyph/core/workspace/fs.py
from __future__ import annotations
import os, shutil, json, uuid, hashlib
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

from .base import WorkspaceBase  # if you split base helpers
# If you haven't made base.py yet, you can keep this file self-contained.

def _default_root_dir() -> str:
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, ".git")):
        return os.path.join(cwd, ".glyph_workspace")
    return os.path.join(cwd, "glyph_workspace")

class FilesystemWorkspace(WorkspaceBase):  # or just `object` if you haven't created base.py yet
    def __init__(self, root_dir: Optional[str] = None, use_uuid: bool = False,
                 custom_paths: Optional[Dict[str, str]] = None):
        if root_dir is None:
            root_dir = _default_root_dir()

        os.makedirs(root_dir, exist_ok=True)
        base_root = root_dir

        # run id
        run_id = (
            datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + str(uuid.uuid4())[:8]
            if use_uuid else "default"
        )

        root_dir_with_run = os.path.join(base_root, run_id)
        os.makedirs(root_dir_with_run, exist_ok=True)

        paths = {
            "input_docx":       os.path.join(root_dir_with_run, "input", "docx"),
            "input_plaintext":  os.path.join(root_dir_with_run, "input", "plaintext"),
            "input_unzipped":   os.path.join(root_dir_with_run, "input", "unzipped"),
            "input_images":     os.path.join(root_dir_with_run, "input", "images"),
            "output_configs":   os.path.join(root_dir_with_run, "output", "configs"),
            "output_docx":      os.path.join(root_dir_with_run, "output", "docx"),
            "output_plaintext": os.path.join(root_dir_with_run, "output", "plaintext"),
        }
        if custom_paths:
            paths.update(custom_paths)

        # Call parent __init__ with keyword arguments
        super().__init__(
            base_root=base_root,
            root_dir=root_dir_with_run,
            run_id=run_id,
            paths=paths,
        )

        # Initialize tag attributes
        self.tag: Optional[str] = None
        self._auto_tag_generated: bool = False

        # Create directories
        for path in self._paths.values():
            # Make dirs only (skip files)
            if os.path.splitext(path)[1] == "":
                os.makedirs(path, exist_ok=True)

    # --- helpers (same as your current class) ---
    def save_json(self, key: str, name: str, data: dict) -> str:
        # Include tag in filename if set
        if self.tag:
            filename = f"{name}_{self.tag}.json"
        else:
            filename = f"{name}.json"
        path = os.path.join(self._paths[key], filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def load_json(self, key: str, name: str) -> dict:
        # Try with tag first if set
        if self.tag:
            tagged_path = os.path.join(self._paths[key], f"{name}_{self.tag}.json")
            if os.path.exists(tagged_path):
                with open(tagged_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        # Fall back to untagged
        path = os.path.join(self._paths[key], f"{name}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_file(self, key: str, src_path: str, dest_name: Optional[str] = None) -> str:
        base_name = dest_name or os.path.basename(src_path)
        # Include tag in filename if set
        if self.tag:
            name, ext = os.path.splitext(base_name)
            base_name = f"{name}_{self.tag}{ext}"
        dest_path = os.path.join(self._paths[key], base_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        return dest_path

    def copy_image(
        self,
        src_path: str,
        image_id: str,
        index: Optional[int] = None,
    ) -> str:
        """
        Copy an image to the input_images directory with proper naming.

        Args:
            src_path: Path to source image file
            image_id: Unique identifier for the image (e.g., "profile", "logo")
            index: Optional index for ordering (e.g., 1 -> "img001_profile.png")

        Returns:
            Destination path of the copied image
        """
        ext = os.path.splitext(src_path)[1] or ".png"
        if index is not None:
            dest_name = f"img{index:03d}_{image_id}{ext}"
        else:
            dest_name = f"{image_id}{ext}"
        return self.save_file("input_images", src_path, dest_name)

    def directory(self, key: str) -> str:
        return self._paths[key]

    def delete_all(self):
        for path in self._paths.values():
            if os.path.exists(path):
                shutil.rmtree(path)
                os.makedirs(path, exist_ok=True)

    def delete_workspace(self):
        if os.path.exists(self.root_dir):
            shutil.rmtree(self.root_dir)

    def delete_root(self):
        if os.path.exists(self.base_root):
            shutil.rmtree(self.base_root)

    def generate_tag_from_docx(self, docx_path: str) -> str:
        """Generate a tag from the DOCX file hash."""
        with open(docx_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash[:8]

    def set_auto_tag_from_docx(self, docx_path: str) -> str:
        """Generate and set a tag from the DOCX file hash if not already set."""
        if self.tag is None:
            self.tag = self.generate_tag_from_docx(docx_path)
            self._auto_tag_generated = True
        return self.tag

    def tagged_intake_and_build_schema(self, src_docx: str):
        """Process a DOCX and generate a tagged schema."""
        from glyph.core.utils.docx_intake import intake_docx
        from glyph.core.schema.build_schema import GlyphSchemaBuilder

        # Set the tag from the DOCX file
        self.set_auto_tag_from_docx(src_docx)

        # Intake the DOCX
        intake_result = intake_docx(src_docx, self)

        # Build the schema
        builder = GlyphSchemaBuilder(
            document_xml_path=str(intake_result.key_files["document_xml"]),
            docx_extract_dir=str(intake_result.unzip_dir),
            source_docx=src_docx,
            tag=self.tag,
        )
        schema = builder.run()

        # Save the schema with tag
        schema_name = f"schema_{self.tag}" if self.tag else "schema"
        schema_path = self.save_json("output_configs", schema_name, schema)

        return schema, schema_path

    def tagged_run_schema(self, schema: dict, output_path: str) -> str:
        """Run a tagged schema to generate a DOCX."""
        from glyph.core.schema_runner.run_schema import GlyphSchemaRunner

        # Use tag from schema if present
        tag = schema.get("tag")
        if tag:
            self.tag = tag

        # Run the schema
        runner = GlyphSchemaRunner(schema)
        return runner.save(output_path, tag=tag)

    def full_tagged_workflow(self, src_docx: str, output_path: str):
        """
        Complete workflow: intake DOCX, build schema, run schema.

        Returns:
            Tuple of (schema_path, output_path, tag)
        """
        # Build the schema
        schema, schema_path = self.tagged_intake_and_build_schema(src_docx)

        # Run the schema
        final_output = self.tagged_run_schema(schema, output_path)

        return schema_path, final_output, self.tag

    def get_tagged_files_info(self) -> dict:
        """
        Get information about tagged files in the workspace.

        Returns:
            Dict with 'tag' and 'files' keys, where 'files' maps
            directory keys to lists of filenames.
        """
        info = {
            "tag": self.tag,
            "files": {}
        }

        if self.tag:
            for key, path in self._paths.items():
                if os.path.exists(path) and os.path.isdir(path):
                    tagged_files = [
                        f for f in os.listdir(path)
                        if self.tag in f
                    ]
                    if tagged_files:
                        info["files"][key] = tagged_files

        return info
