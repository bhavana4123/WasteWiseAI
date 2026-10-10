"""Build a CPython 3.12 Linux/x86_64 Lambda ZIP, even when invoked on Windows.

Only binary manylinux wheels are accepted, preventing Windows native extensions
from entering the artifact. No datasets are regenerated and no AWS calls are made.
"""
import argparse
import hashlib
from importlib.metadata import distributions
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
MAX_UNCOMPRESSED = 250 * 1024 * 1024
MAX_DIRECT_UPLOAD = 50 * 1024 * 1024


def runtime_files():
    for directory in ('backend', 'engine', 'data'):
        for path in sorted((ROOT / directory).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            if directory != 'data' and path.suffix not in ('.py', '.txt'):
                continue
            yield path, path.relative_to(ROOT).as_posix()
    yield ROOT / 'scripts/common.py', 'scripts/common.py'


def add_file(archive, path, name):
    info = ZipInfo(name)
    info.create_system = 3  # POSIX permissions regardless of the build host.
    info.external_attr = (stat.S_IFREG | 0o444) << 16
    info.compress_type = ZIP_DEFLATED
    archive.writestr(info, path.read_bytes())


def build(output, wheelhouse=None):
    output = output.resolve()
    if not output.is_relative_to(ROOT):
        raise ValueError('Output must stay inside the project workspace')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Owned temporary paths stay beneath the verified workspace output directory.
    # Failed downloads never publish a partial deployment ZIP.
    with tempfile.TemporaryDirectory(prefix='lambda-build-', dir=output.parent) as temp:
        stage = Path(temp)
        deps = stage / 'dependencies'
        command = [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                   '--retries', '0', '--timeout', '20', '--no-compile',
                   '--platform', 'manylinux2014_x86_64', '--implementation', 'cp',
                   '--python-version', '3.12', '--abi', 'cp312', '--only-binary=:all:',
                   '--target', str(deps), '-r', str(ROOT / 'backend/requirements-lambda.txt')]
        if wheelhouse:
            command += ['--no-index', '--find-links', str(wheelhouse.resolve())]
        subprocess.run(command, check=True)
        artifact = stage / 'wastewise-lambda.zip'
        with ZipFile(artifact, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(deps.rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                    if path.suffix.lower() in ('.pyd', '.dll'):
                        raise ValueError(f'Windows native dependency rejected: {path.name}')
                    add_file(archive, path, path.relative_to(deps).as_posix())
            for path, name in runtime_files():
                add_file(archive, path, name)
        with ZipFile(artifact) as archive:
            uncompressed = sum(info.file_size for info in archive.infolist())
            if uncompressed > MAX_UNCOMPRESSED:
                raise ValueError('Package exceeds the 250 MiB uncompressed Lambda limit')
            if archive.testzip() is not None:
                raise ValueError('ZIP integrity check failed')
        metadata = {
            'runtime': 'python3.12', 'architecture': 'x86_64',
            'handler': 'backend.lambda_handler.handler',
            'compressed_bytes': artifact.stat().st_size,
            'uncompressed_bytes': uncompressed,
            'requires_s3_upload': artifact.stat().st_size > MAX_DIRECT_UPLOAD,
            'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
            'dependencies': {dist.metadata['Name']: dist.version
                             for dist in distributions(path=[str(deps)])},
        }
        artifact.replace(output)
        output.with_suffix('.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        print(json.dumps({'artifact': str(output), **metadata}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/lambda/wastewise-lambda.zip')
    parser.add_argument('--wheelhouse', type=Path, help='Offline directory of Linux-compatible wheels')
    args = parser.parse_args()
    build(args.output, args.wheelhouse)
