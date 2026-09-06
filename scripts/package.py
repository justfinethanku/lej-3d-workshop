#!/usr/bin/env python3
"""Validate and build the complete public skill archive (standard library only)."""
from pathlib import Path
import hashlib
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skill' / 'lej-3d-workshop'


def build():
    version = (ROOT / 'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must be a numeric semantic version')
    entry = (SKILL / 'SKILL.md').read_text()
    for marker in ('<!-- USER_CONFIG_START -->', '<!-- USER_CONFIG_END -->'):
        if entry.count(marker) != 1:
            raise ValueError(f'Expected exactly one {marker}')
    if entry.index('<!-- USER_CONFIG_START -->') > entry.index('<!-- USER_CONFIG_END -->'):
        raise ValueError('User config markers are reversed')
    sources = sorted(p for p in SKILL.rglob('*') if p.is_file())
    for source in sources:
        if source.is_symlink():
            raise ValueError(f'Symlink is not a portable package file: {source}')
        if source.suffix == '.md':
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', source.read_text()):
                if target.startswith(('https://', 'http://', '#', 'mailto:')):
                    continue
                destination = (source.parent / target.split('#')[0]).resolve()
                if not destination.is_relative_to(SKILL.resolve()) or not destination.is_file():
                    raise ValueError(f'Broken or external local reference: {source}: {target}')
    content = {f'lej-3d-workshop/{p.relative_to(SKILL).as_posix()}': p.read_bytes() for p in sources}
    for name in ('LICENSE', 'VERSION'):
        content[f'lej-3d-workshop/{name}'] = (ROOT / name).read_bytes()
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    archive = output / f'lej-3d-workshop-v{version}.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(content.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data)
    with zipfile.ZipFile(archive) as bundle:
        assert set(bundle.namelist()) == set(content)
        for name, data in content.items():
            assert bundle.read(name) == data, f'Archive content differs: {name}'
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(f'{checksum}  {archive.name}\n')
    print(f'Validated {len(sources)} skill files; verified {len(content)} archive entries')
    print(f'{checksum}  {archive.name}')


if __name__ == '__main__':
    build()
