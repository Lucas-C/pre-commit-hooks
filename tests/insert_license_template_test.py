import os

import pytest

from pre_commit_hooks.insert_license import main as insert_license


def test_skip_default_license_template(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    template = tmp_path / "LICENSE.txt"
    original = b"Copyright 2024 Example.\r\nAll rights reserved.\r\n"
    template.write_bytes(original)

    assert insert_license(["LICENSE.txt"]) == 0
    assert template.read_bytes() == original
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("license_filepath", "source_filepath"),
    (
        (".github/LICENSE", ".github/LICENSE"),
        ("./.github/LICENSE", ".github/LICENSE"),
        (".github/LICENSE", "./.github/../.github/LICENSE"),
        ("{root}/.github/LICENSE", ".github/LICENSE"),
        (".github/LICENSE", "{root}/.github/LICENSE"),
    ),
)
def test_skip_explicit_license_template(
    tmp_path, monkeypatch, capsys, license_filepath, source_filepath
):
    monkeypatch.chdir(tmp_path)
    template = tmp_path / ".github" / "LICENSE"
    template.parent.mkdir()
    original = b"Copyright 2024 Example.\r\nAll rights reserved.\r\n"
    template.write_bytes(original)

    assert (
        insert_license(
            [
                "--license-filepath",
                license_filepath.format(root=tmp_path),
                source_filepath.format(root=tmp_path),
            ]
        )
        == 0
    )
    assert template.read_bytes() == original
    assert capsys.readouterr().out == ""


def test_skip_all_license_templates_but_process_sources(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    template = tmp_path / "LICENSE"
    alternative = tmp_path / "LICENSE.other"
    source = tmp_path / "src" / "LICENSE"
    template.write_text("Primary license.\n", encoding="utf8")
    alternative.write_text("Alternative license.\n", encoding="utf8")
    source.parent.mkdir()
    source.write_text("source contents\n", encoding="utf8")
    args = [
        "--license-filepath",
        "LICENSE",
        "--license-filepath",
        "LICENSE.other",
        "LICENSE",
        "src/LICENSE",
        "LICENSE.other",
    ]

    assert insert_license(args) == 1
    assert template.read_text(encoding="utf8") == "Primary license.\n"
    assert alternative.read_text(encoding="utf8") == "Alternative license.\n"
    assert source.read_text(encoding="utf8") == (
        "# Primary license.\n\nsource contents\n"
    )
    assert "['src/LICENSE']" in capsys.readouterr().out
    assert insert_license(args) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("link_type", ("symlink", "hardlink"))
def test_skip_license_template_link(tmp_path, link_type, capsys):
    template = tmp_path / "LICENSE.txt"
    alias = tmp_path / "alias.txt"
    original = b"Copyright 2024 Example.\nAll rights reserved.\n"
    template.write_bytes(original)
    try:
        if link_type == "symlink":
            alias.symlink_to(template)
        else:
            os.link(template, alias)
    except OSError as error:
        pytest.skip(f"Cannot create {link_type}: {error}")

    assert insert_license(["--license-filepath", str(template), str(alias)]) == 0
    assert template.read_bytes() == original
    assert alias.read_bytes() == original
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("mode", ("--use-current-year", "--remove-header"))
def test_skip_license_template_in_other_modes(tmp_path, capsys, mode):
    template = tmp_path / "LICENSE.txt"
    original = b"Copyright 2000 Example.\nAll rights reserved.\n"
    template.write_bytes(original)

    assert (
        insert_license(
            [
                "--license-filepath",
                str(template),
                "--comment-style",
                "",
                mode,
                str(template),
            ]
        )
        == 0
    )
    assert template.read_bytes() == original
    assert capsys.readouterr().out == ""
