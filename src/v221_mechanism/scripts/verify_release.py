"""Verify the v2.2.1 immutable private research release."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from v22core.gpu_handoff import release_check
root=Path(__file__).resolve().parents[1]
files=release_check(root)
print('V221_RELEASE_HASH_PASS',len(files),'files')
