#!/bin/bash

# Step 1: Clean any old builds
rm -rf _build/html/

# Step 2: Change to the docs directory
cd docs

# Step 3: Build the MkDocs guide first (creates the '_build/html' folder)
mkdocs build --site-dir ../_build/html

# Step 4: Build Sphinx directly into the compiled MkDocs '_build/api' folder
sphinx-build -b html api ../_build/html/api

# Step 5: Return to the root directory
cd ..

# Copy to the final build directory
cp -a ./_build/html/. ../seanslma.github.io/nemas/
