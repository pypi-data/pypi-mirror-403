import re, hashlib, datetime, platform
from pathlib import Path
from os.path import abspath

import yaml  # pip install pyyaml

this_dir = Path(__file__).parent
files_dir = this_dir / 'files'

def is_subpath(parent_path, child_path) -> bool:
    parent = Path(parent_path).resolve()
    child = Path(child_path).resolve()
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False

system_environment = dict(
    operating_system = platform.system(),
    operating_system_version = platform.release(),
    python_version = platform.python_version(),
)

gap_symbol = '----------------------------------------------------------------------'

def update_files_hashes(root_dir: str):
    if not is_subpath(files_dir, root_dir):
        raise ValueError(f"非法路径：{root_dir} 不在 {files_dir} 下")
    print(f"正在更新文件夹 | {root_dir}")
    print(gap_symbol)
    files: list[Path] = []
    for x in list(Path(abspath(root_dir)).rglob("*")):
        if x.is_file():
            if re.search(r'\.hash\.yaml$', x.as_posix(), re.I):
                print(f"删除哈希文件 | {x}")
                x.unlink()
            else:
                files.append(x)
    print(gap_symbol)
    for x in files:
        print(f"更新哈希文件 | {x}")
        x_bytes = x.read_bytes()
        result = {
            'file_info': {
                'size': x.stat().st_size,
                'sha-512': hashlib.sha512(x_bytes).hexdigest(),
                'sha3-512': hashlib.sha3_512(x_bytes).hexdigest(),
            },
            'system_environment': system_environment,
            'generated_date_utc': datetime.date.today().isoformat(),
        }
        result = yaml.dump(result, Dumper=yaml.SafeDumper, indent=4, allow_unicode=True, sort_keys=False)
        Path(f"{x}.hash.yaml").write_text(result, encoding='utf-8')
    print(gap_symbol)
    print('更新完成')

if __name__ == '__main__':
    update_files_hashes(rf'C:\bpath\pypi_arts\arts\skybox\files')
