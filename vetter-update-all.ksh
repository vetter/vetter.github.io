#!/bin/ksh -x

uv run --with pandas --with requests --with pyyaml  vetter-update-pres.py
uv run --with pandas --with requests --with pyyaml  vetter-update-service.py
uv run --with pandas --with requests --with pyyaml  vetter-update-software.py

jupyter nbconvert --to notebook --execute talkmap.ipynb --output talkmap_out.ipynb

