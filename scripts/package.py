#!/usr/bin/env python3
"""Validate and build the complete public skill archive (standard library only)."""
from pathlib import Path
import hashlib
import posixpath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {'__pycache__', 'cadquery-verification'}


def reject_symlinks(path, root):
    """Check each component before reading inputs or writing release artifacts."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f'Symlink is not a portable package path: {current}')


def collect_content(root):
    """Snapshot the complete release once, keyed by its installed relative paths."""
    skill = root / 'skill' / 'lej-3d-workshop'
    for path in (root / 'VERSION', root / 'LICENSE', skill / 'SKILL.md'):
        reject_symlinks(path, root)
    content = {name: (root / name).read_bytes() for name in ('LICENSE', 'VERSION')}
    version = content['VERSION'].decode().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must be a numeric semantic version')
    # Package every maintained file in the skill folder. Hidden files, caches and
    # generated verification runs are never distributable.
    skill_files = 0
    for source in sorted(skill.rglob('*')):
        if source.suffix == '.pyc' or any(
                part.startswith('.') or part in EXCLUDED_DIRS
                for part in source.relative_to(skill).parts):
            continue
        reject_symlinks(source, root)
        if source.is_file():
            name = source.relative_to(skill).as_posix()
            if name in content:
                raise ValueError(f'Duplicate release path: {name}; keep release metadata at the repository root')
            content[name] = source.read_bytes()
            skill_files += 1
    entry = content['SKILL.md'].decode('utf-8')
    for marker in ('<!-- USER_CONFIG_START -->', '<!-- USER_CONFIG_END -->'):
        if entry.count(marker) != 1:
            raise ValueError(f'Expected exactly one {marker}')
    if entry.index('<!-- USER_CONFIG_START -->') > entry.index('<!-- USER_CONFIG_END -->'):
        raise ValueError('User config markers are reversed')
    for name, data in content.items():
        if name.endswith('.md'):
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', data.decode('utf-8')):
                if target.startswith(('https://', 'http://', '#', 'mailto:')):
                    continue
                destination = posixpath.normpath(posixpath.join(
                    posixpath.dirname(name), target.split('#', 1)[0]))
                if destination not in content:
                    raise ValueError(f'Linked file is missing or not packaged: {name}: {target}')
    return version, {f'lej-3d-workshop/{name}': data for name, data in content.items()}, skill_files


def build(root=ROOT):
    version, content, skill_files = collect_content(root)
    output = root / 'dist'
    archive = output / f'lej-3d-workshop-v{version}.zip'
    checksum_file = output / 'SHA256SUMS'
    for path in (output, archive, checksum_file):
        reject_symlinks(path, root)
    output.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(content.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data)
    with zipfile.ZipFile(archive) as bundle:
        if set(bundle.namelist()) != set(content):
            raise ValueError('Archive entry list differs from sources')
        for name, data in content.items():
            if bundle.read(name) != data:
                raise ValueError(f'Archive content differs: {name}')
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum_file.write_text(f'{checksum}  {archive.name}\n')
    print(f'Validated {skill_files} skill files; verified {len(content)} archive entries')
    print(f'{checksum}  {archive.name}')


if __name__ == '__main__':
    build()
