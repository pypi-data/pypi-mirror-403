#!/bin/bash
# Delete any existing dist or egg dirs and run from the root of the repository 
python -m build
read -p "Package built, check dist/*, press [ENTER] to continue"
python -m twine upload --repository testpypi dist/*
read -p "Uploaded to PyPi test, press [ENTER] to continue"
python -m twine upload dist/*
echo "**** Finished ****"
