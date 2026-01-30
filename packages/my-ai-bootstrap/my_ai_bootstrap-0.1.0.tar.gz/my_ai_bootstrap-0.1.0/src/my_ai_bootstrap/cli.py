from __future__ import annotations
import os, sys, subprocess

FORGEJO_SIMPLE = "https://git.mystrotamer.com/api/packages/ai/pypi/simple"
PYPI_SIMPLE = "https://pypi.org/simple"

def _run(*args: str) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", *args])

def main() -> int:
    # 1) configure pip (once)
    _run("config", "set", "global.index-url", FORGEJO_SIMPLE)
    _run("config", "set", "global.extra-index-url", PYPI_SIMPLE)

    # 2) install/upgrade toolchain entrypoint
    _run("install", "-U", "my-ai-tools")

    print("✅ Done. You can now run: my-ai doctor | my-ai chat | my-ai learn de")
    return 0
