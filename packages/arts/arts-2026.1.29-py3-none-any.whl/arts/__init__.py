import re
from os.path import abspath
from pathlib import Path

def search_files(root_dir: Path|str, pattern: str=r'', *, flags=0):
    '''
    搜索结果不包含自身
    '''
    for x in Path(abspath(root_dir)).rglob("*"):
        if not pattern or re.search(pattern, x.as_posix(), flags):
            yield x

test_dir = Path(__file__).parent
