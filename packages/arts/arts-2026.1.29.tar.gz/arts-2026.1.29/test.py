import re

from arts import search_files  # 导入用来查找路径的函数
from arts import test_dir  # 导入用来测试的目录

# 查找所有.py文件
results = search_files(root_dir=test_dir, pattern=r'\.py$', flags=0)
for x in results:
    print(x)

# 查找所有文件名包含'README'的文件, 忽略大小写
results = search_files(root_dir=test_dir, pattern=r'README', flags=re.I)
for x in results:
    print(x)
