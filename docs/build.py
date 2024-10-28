from subprocess import call
from pathlib import Path
import shlex

workdir = Path(__file__).parent.parent
call(
    shlex.split(
        "poetry run sphinx-apidoc -o docs/source thundra_io thundra_io.button thundra_io.core thundra_io.profiler thundra_io.storage"
    )
)
call(shlex.split("poetry run make html"), cwd=workdir / "docs")
with open(workdir / "docs/_build/html/.nojekyll", "wb") as file:
    file.write(b"")
