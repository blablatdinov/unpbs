import subprocess
import pytest
from pathlib import Path
import os
import subprocess
from collections.abc import Generator
from pathlib import Path
from shutil import copy2

import pytest
from _pytest.legacypath import TempdirFactory


@pytest.fixture(scope='module')
def current_dir() -> Path:
    return Path().absolute()


@pytest.fixture(scope='module')
def _test_dir(tmpdir_factory: TempdirFactory, current_dir: str) -> Generator[None, None, None]:
    tmp_path = tmpdir_factory.mktemp('test')
    copy2(Path('tests/fixtures/file.py.txt'), tmp_path / 'file.py')
    os.chdir(tmp_path)
    print(tmp_path)
    subprocess.run(['python3', '-m', 'venv', 'venv'], check=True)
    subprocess.run(['venv/bin/pip', 'install', 'pip', '-U'], check=True)
    subprocess.run(['venv/bin/pip', 'install', str(current_dir)], check=True)
    yield
    os.chdir(current_dir)


@pytest.mark.usefixtures("_test_dir")
def test(current_dir: Path):
    subprocess.run(['venv/bin/pip', 'install', str(current_dir)], check=True)
    got = subprocess.run(
        ['venv/bin/unpbs', 'file.py'],
        stdout=subprocess.PIPE,
        check=False,
    )
    assert got.returncode == 0
    assert got.stdout.decode('utf-8') == '\n'.join([
        'bar',
        '  fan_in: 1',
        '  fan_out: 0',
        'foo',
        '  fan_in: 0',
        '  fan_out: 1\n',
    ])
