set -e

rm -rf build dist medsenger_api.egg-info
python3 -m build
twine check dist/*
twine upload dist/*
