from pathlib import Path
from lumpy_log import OUTPUT_CHANGELOGS_DIR, OUTPUT_TESTRESULTS_DIR
from lumpy_log.utils import _rebuild_index


def prepare_sample_entries(base: Path):
    commits_dir = base / OUTPUT_CHANGELOGS_DIR
    tests_dir = base / OUTPUT_TESTRESULTS_DIR
    commits_dir.mkdir()
    tests_dir.mkdir()

    commit_file = commits_dir / "20240101_1200_commit.md"
    commit_file.write_text("# Commit One\nBody one", encoding="utf-8")

    test_file = tests_dir / "20240102_1200_test.md"
    test_file.write_text("# Test One\nBody test", encoding="utf-8")

    return commit_file, test_file


def test_devlog_not_created_without_flag(tmp_path):
    prepare_sample_entries(tmp_path)

    _rebuild_index(str(tmp_path), output_formats=["obsidian"])

    assert not (tmp_path / "devlog.md").exists()


def test_devlog_contains_all_entries_in_order(tmp_path):
    prepare_sample_entries(tmp_path)

    _rebuild_index(str(tmp_path), output_formats=["devlog"])

    devlog_path = tmp_path / "devlog.md"
    assert devlog_path.exists()

    content = devlog_path.read_text(encoding="utf-8")
    assert "# Commit One" in content
    assert "# Test One" in content
    assert content.index("# Commit One") < content.index("# Test One")


def test_devlog_respects_changelog_order(tmp_path):
    commits_dir = tmp_path / OUTPUT_CHANGELOGS_DIR
    tests_dir = tmp_path / OUTPUT_TESTRESULTS_DIR
    commits_dir.mkdir()
    tests_dir.mkdir()

    early_commit = commits_dir / "20240101_0800_commit.md"
    early_commit.write_text("# Early Commit\nOld body", encoding="utf-8")
    
    late_commit = commits_dir / "20240103_0900_commit.md"
    late_commit.write_text("# Late Commit\nNew body", encoding="utf-8")

    mid_test = tests_dir / "20240102_1200_test.md"
    mid_test.write_text("# Mid Test\nResult body", encoding="utf-8")

    _rebuild_index(str(tmp_path), changelog_order=True, output_formats=["devlog"])

    content = (tmp_path / "devlog.md").read_text(encoding="utf-8")
    assert "# Late Commit" in content
    assert "# Early Commit" in content
    assert "# Mid Test" in content

    assert content.index("# Late Commit") < content.index("# Mid Test")
    assert content.index("# Mid Test") < content.index("# Early Commit")
