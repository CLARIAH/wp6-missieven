#!/bin/sh

cd ~/github/clariah/wp6-missieven/programs

python3 trimTei.py 0
python3 trimTei.py 1
python3 trimTei.py 2
python3 trimTei.py 3
python3 trimTei.py 4

python3 trimPdf.py pdf
python3 trimPdf.py struct
python3 trimPdf.py fine
python3 trimPdf.py xml

python3 tfFromTrim.py
python3 tfFromTrim.py loadonly

# do not forget to run the notebook map.ipynb

# to generate static search interface and run it locally:
# text-fabric-make clariah/wp6-missieven serve

# in order to publish on gh-pages:
# text-fabric-make clariah/wp6-missieven ship
