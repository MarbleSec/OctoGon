import os
import stat
import subprocess

script = os.path.abspath("ChmodSetup.sh")

st = os.stat(script)
os.chmod(script, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

result = subprocess.run([script])
print(f"Script exited with code {result.returncode}")
