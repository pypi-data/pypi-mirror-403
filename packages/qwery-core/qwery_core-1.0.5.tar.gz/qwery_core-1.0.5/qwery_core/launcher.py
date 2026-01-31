import os
import sys
import subprocess
import tempfile
import shutil
import stat


def detect_env():
    if "ANDROID_ROOT" in os.environ:
        return "android"

    if os.path.exists("/proc/version"):
        with open("/proc/version", "r") as f:
            v = f.read().lower()
            if "ish" in v or "musl" in v:
                return "ish"

    return None


def chmod_exec(path):
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)


def main():
    env = detect_env()
    if not env:
        print("Unsupported system")
        sys.exit(1)

    base = os.path.dirname(__file__)

    if env == "android":
        exe = os.path.join(base, "bin", "android", "Devil")
        lib_path = os.path.join(base, "bin", "android")
    else:
        exe = os.path.join(base, "bin", "ish", "Devil")
        lib_path = os.path.join(base, "bin", "ish")

    tmp = tempfile.mkdtemp(prefix="qwery_")
    run = os.path.join(tmp, "Devil")

    shutil.copy2(exe, run)
    chmod_exec(run)

    envs = os.environ.copy()

    envs["PYTHONHOME"] = sys.prefix
    envs["PYTHON_EXECUTABLE"] = sys.executable

    envs["LD_LIBRARY_PATH"] = (
        envs.get("LD_LIBRARY_PATH", "") + ":" + lib_path
    )

    subprocess.run(
        [run, *sys.argv[1:]],
        cwd=tmp,
        env=envs,
        check=False
    )