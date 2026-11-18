from pathlib import Path
import shutil
root=Path(__file__).resolve().parent.parent
src=root/'data';dst=root/'public'/'data'
if dst.exists():shutil.rmtree(dst)
shutil.copytree(src,dst)
print('Copied latest and historical data to static public bundle')
