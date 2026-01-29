#!/bin/bash
pip3 install hatch wheel twine

# Build the package
hatch build

# Upload to pypi
twine upload dist/*