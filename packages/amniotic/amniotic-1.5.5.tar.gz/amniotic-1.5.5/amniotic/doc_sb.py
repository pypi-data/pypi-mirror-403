import subprocess
import sys

from amniotic.paths import paths


from mkdocs.commands import serve

serve.serve(str(paths.repo/'mkdocs.yml'), dev_addr="0.0.0.0:8080", livereload=True)#docs_dir=str(paths.repo)
