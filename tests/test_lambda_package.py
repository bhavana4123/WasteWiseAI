"""ZIP layout and failure safety; mocked downloads are not runtime validation."""
import importlib.util
from pathlib import Path
import stat
import subprocess
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lambda_builder', ROOT / 'scripts/build_lambda_package.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_linux_target_and_complete_read_only_scientific_layout(tmp_path, monkeypatch):
    def simulated_install(command, check):
        assert check
        assert command[command.index('--platform') + 1] == 'manylinux2014_x86_64'
        assert command[command.index('--python-version') + 1] == '3.12'
        assert '--only-binary=:all:' in command
        deps = Path(command[command.index('--target') + 1])
        deps.mkdir()
        (deps / 'test-only-dependency.txt').write_text('Package layout test, not a real dependency')
    monkeypatch.setattr(builder.subprocess, 'run', simulated_install)
    output = tmp_path / 'layout-test.zip'
    builder.build(output)
    with ZipFile(output) as archive:
        assert 'backend/lambda_handler.py' in archive.namelist()
        assert 'scripts/common.py' in archive.namelist()
        assert not any(name.startswith(('frontend/', 'reports/')) for name in archive.namelist())
        for path in (ROOT / 'data').rglob('*'):
            if path.is_file():
                name = path.relative_to(ROOT).as_posix()
                assert archive.read(name) == path.read_bytes()
                mode = archive.getinfo(name).external_attr >> 16
                assert stat.S_IMODE(mode) == 0o444


def test_windows_native_dependency_rejected(tmp_path, monkeypatch):
    def simulated_install(command, check):
        deps = Path(command[command.index('--target') + 1])
        deps.mkdir()
        (deps / 'windows-extension.pyd').write_bytes(b'not a Linux wheel')
    monkeypatch.setattr(builder.subprocess, 'run', simulated_install)
    output = tmp_path / 'invalid.zip'
    with pytest.raises(ValueError, match='Windows native'):
        builder.build(output)
    assert not output.exists()


def test_failed_download_does_not_overwrite_existing_artifact(tmp_path, monkeypatch):
    output = tmp_path / 'existing.zip'
    output.write_bytes(b'previous artifact')
    def failed_download(command, check):
        raise subprocess.CalledProcessError(1, command)
    monkeypatch.setattr(builder.subprocess, 'run', failed_download)
    with pytest.raises(subprocess.CalledProcessError):
        builder.build(output)
    assert output.read_bytes() == b'previous artifact'
    assert not list(tmp_path.glob('lambda-build-*'))


def test_output_cannot_leave_workspace():
    with pytest.raises(ValueError, match='workspace'):
        builder.build(ROOT.parent / 'outside-workspace.zip')
