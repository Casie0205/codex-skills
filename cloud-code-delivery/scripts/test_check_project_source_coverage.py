#!/usr/bin/env python3
"""Tests for Visual Studio source coverage checks."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("check_project_source_coverage.py")


PROJECT_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <ItemGroup>
    <ClCompile Include="..\\..\\src\\Shared.c" />
    {required_item}
  </ItemGroup>
</Project>
"""


class SourceCoverageTests(unittest.TestCase):
    def run_check(
        self,
        root: Path,
        configuration: str = "Release",
        platform: str = "Win32",
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--repo",
                str(root),
                "--project-root",
                str(root / "proj"),
                "--anchor-source",
                r"src\Shared.c",
                "--required-source",
                r"src\Required.c",
                "--configuration",
                configuration,
                "--platform",
                platform,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def write_project(self, root: Path, required_item: str = "") -> Path:
        project_dir = root / "proj" / "app"
        project_dir.mkdir(parents=True)
        (root / "src").mkdir()
        (root / "src" / "Shared.c").write_text("", encoding="utf-8")
        (root / "src" / "Required.c").write_text("", encoding="utf-8")
        project = project_dir / "app.vcxproj"
        project.write_text(
            PROJECT_TEMPLATE.format(required_item=required_item),
            encoding="utf-8",
        )
        return project

    def test_rejects_project_missing_required_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_project(root)
            result = self.run_check(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MISSING", result.stdout)

    def test_accepts_project_with_required_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_project(
                root, '<ClCompile Include="..\\..\\src\\Required.c" />'
            )
            result = self.run_check(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("OK", result.stdout)

    def test_rejects_required_source_listed_only_as_clinclude(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_project(
                root, '<ClInclude Include="..\\..\\src\\Required.c" />'
            )
            result = self.run_check(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MISSING", result.stdout)

    def test_rejects_excluded_from_build_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_project(
                root,
                '<ClCompile Include="..\\..\\src\\Required.c">'
                "<ExcludedFromBuild>true</ExcludedFromBuild>"
                "</ClCompile>",
            )
            result = self.run_check(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MISSING", result.stdout)

    def test_accepts_required_source_matching_configuration_condition(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_project(
                root,
                '<ClCompile Include="..\\..\\src\\Required.c" '
                'Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'" />',
            )
            result = self.run_check(root)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_required_source_for_other_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_project(
                root,
                '<ClCompile Include="..\\..\\src\\Required.c" '
                'Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'" />',
            )
            result = self.run_check(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MISSING", result.stdout)

    def test_expands_project_directory_property(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_project(
                root,
                '<ClCompile Include="$(ProjectDir)..\\..\\src\\Required.c" />',
            )
            result = self.run_check(root)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_unknown_anchor_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project_dir = root / "proj" / "app"
            project_dir.mkdir(parents=True)
            (root / "src").mkdir()
            (root / "src" / "Required.c").write_text("", encoding="utf-8")
            project = project_dir / "app.vcxproj"
            project.write_text(
                '<?xml version="1.0" encoding="utf-8"?>'
                '<Project xmlns="http://schemas.microsoft.com/developer/msbuild/2003">'
                "<ItemGroup>"
                '<ClCompile Include="..\\..\\src\\Required.c" />'
                "</ItemGroup>"
                "</Project>",
                encoding="utf-8",
            )
            result = self.run_check(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no evaluated .vcxproj consumes", result.stderr)


if __name__ == "__main__":
    unittest.main()
