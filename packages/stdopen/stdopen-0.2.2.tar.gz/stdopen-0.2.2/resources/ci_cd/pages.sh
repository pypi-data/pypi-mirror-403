#!/bin/sh
# This is assumed to be running from the root of the repo
echo "[pages] running in: $PWD"

# Ensure the documentation build directory is present
mkdir -p ./docs/build

# Copy files to docs/source/ (your originals remain unchanged)
cp README.md docs/source/getting_started.md
cp CHANGELOG.md docs/source/changelog.md

# Your existing path fixes
sed -i 's/\.\/docs\/source\///' docs/source/getting_started.md
sed -i 's|src="\./resources/images|src="./_static/images|' docs/source/getting_started.md

# Normalize case in links before preprocessing (e.g., force lowercase for <file>)
sed -i 's/(\([^#]*\)\.md)/(\L\1.md)/g' docs/source/*.md  # Lowercase the file part in links without anchors
sed -i 's/(\([^#]*\)\.md#\([^)]*\))/(\L\1.md#\2)/g' docs/source/*.md  # Same for links with anchors

# Preprocess links in ALL .md files under docs/source/ (adjust glob if needed)
for md_file in docs/source/*.md; do
    # Replace [text](file.md) with {doc}`text <file>`
    sed -i 's/\[\([^]]*\)\](\([^#]*\)\.md)/{doc}`\1 <\2>`/g' "$md_file"

    # Replace [text](file.md#anchor) with {ref}`text </file#anchor>`
    sed -i 's/\[\([^]]*\)\](\([^#]*\)\.md#\([^)]*\))/{ref}`\1 <\/\2#\3>`/g' "$md_file"
done

# mkdir -p docs/source/data_dict
# for i in ./resources/data_dict/*.txt; do
#     outfile="$(basename "$i" | sed 's/\.txt/.rst/')"
#     doc-column-list "$i" ./docs/source/data_dict/"$outfile"
# done

# python -c 'print("***** importing paper scraper *****"); import paper_scraper'
cd docs
make html
cd ..
echo "[pages] removing public"

# if [[ -e public ]]; then
#     rm -r public
# fi
echo "[pages] creating public"
mkdir -p public
echo "[pages] moving HTML to public"
mv docs/build/html/* public/
echo "[pages] PWD: $PWD"
echo "[pages] contents of public"
ls "$PWD"/public
