#!/bin/sh -x
set -e

uv run --with pandas --with requests --with pyyaml  vetter-update-pres.py
uv run --with pandas --with requests --with pyyaml  vetter-update-service.py
uv run --with pandas --with requests --with pyyaml  vetter-update-software.py

uv run --with pandas --with requests --with pyyaml --with python-frontmatter --with geopy --with getorg vetter-update-talkmap.py

