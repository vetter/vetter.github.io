#!/bin/ksh -x

python3 vetter-update-pres.py
python3 vetter-update-service.py
python3 vetter-update-software.py

jupyter nbconvert --to notebook --execute talkmap.ipynb --output talkmap_out.ipynb

