## Test local

import sys
from pathlib import Path

repo = Path(r"E:/bja_utils_dev").resolve()
sys.path.insert(0, str(repo))

import bja_utils
print(bja_utils.__file__)