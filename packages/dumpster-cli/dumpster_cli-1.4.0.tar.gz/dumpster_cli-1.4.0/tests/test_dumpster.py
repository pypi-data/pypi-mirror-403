from __future__ import annotations

from pathlib import Path
import yaml
import pytest

from dumpster.const import FILE_SEPARATOR
from dumpster.api import dump, load_config
from dumpster.models import DumpsterConfig


def test_load_config_ignores_dumps(tmp_path: Path):
    cfg = {
        "output": "root.txt",
        "extensions": [".py"],
        "dumps": [{"name": "ui", "contents": ["a.py"]}],
    }
    cfg_path = tmp_path / "dump.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    c = load_config(cfg_path)
    assert isinstance(c, DumpsterConfig)
    assert c.output == "root.txt"
    assert c.extensions == [".py"]


def test_single_config_mode_writes_root_output(tmp_path: Path):
    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")

    cfg = {
        "output": "sources.txt",
        "extensions": [".py"],
        "contents": ["a.py"],
    }
    cfg_path = tmp_path / "dump.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    outs = dump(root_path=tmp_path, config_file=cfg_path)
    assert outs == [tmp_path / "sources.txt"]
    content = (tmp_path / "sources.txt").read_text(encoding="utf-8")
    assert f"{FILE_SEPARATOR} a.py" in content


def test_multi_dump_mode_defaults_apply_except_output(tmp_path: Path):
    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("print('b')\n", encoding="utf-8")

    cfg = {
        # should NOT be inherited by items
        "output": "root-ignored.txt",
        # defaults should be inherited
        "extensions": [".py"],
        "header": "H",
        "dumps": [
            {"name": "ui", "contents": ["a.py"]},
            {"name": "api", "contents": ["b.py"], "output": "api-custom.txt"},
        ],
    }
    cfg_path = tmp_path / "dump.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    outs = dump(root_path=tmp_path, config_file=cfg_path)

    # ui has no output -> slug(name).txt
    ui_out = tmp_path / ".dumpster/ui.txt"
    api_out = tmp_path / "api-custom.txt"

    assert ui_out in outs
    assert api_out in outs

    ui_content = ui_out.read_text(encoding="utf-8")
    api_content = api_out.read_text(encoding="utf-8")

    assert f"{FILE_SEPARATOR} a.py" in ui_content
    assert "H" in ui_content  # header default inherited

    assert f"{FILE_SEPARATOR} b.py" in api_content
    assert "H" in api_content  # header default inherited

    # root output must not be created in batch mode unless explicitly targeted
    assert not (tmp_path / "root-ignored.txt").exists()


def test_multi_dump_mode_name_selection_regex(tmp_path: Path):
    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("print('b')\n", encoding="utf-8")

    cfg = {
        "extensions": [".py"],
        "dumps": [
            {"name": "ui-core", "contents": ["a.py"]},
            {"name": "backend", "contents": ["b.py"]},
        ],
    }
    cfg_path = tmp_path / "dump.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    outs = dump(root_path=tmp_path, config_file=cfg_path, name="ui.*")

    assert outs == [tmp_path / ".dumpster/ui-core.txt"]
    assert (tmp_path / ".dumpster/ui-core.txt").exists()
    assert not (tmp_path / ".dumpster/backend.txt").exists()


def test_multi_dump_mode_name_selection_no_match_raises(tmp_path: Path):
    cfg = {
        "extensions": [".py"],
        "dumps": [{"name": "ui", "contents": ["x.py"]}],
    }
    cfg_path = tmp_path / "dump.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    with pytest.raises(ValueError):
        dump(root_path=tmp_path, config_file=cfg_path, name="api.*")
