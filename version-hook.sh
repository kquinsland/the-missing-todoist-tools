#!/usr/bin/env bash
##
# very simple git-commit hook to update the version string
VERSION_FILE="tdt/version.py"


TAG=$(git describe --abbrev=0 --tags ${TAG_COMMIT} 2>/dev/null || true)
COMMIT=$(git rev-parse --short HEAD)
DATE=$(git log -1 --format=%cd --date=format:"%Y%m%d")
V="$TAG-$COMMIT-$DATE"

echo "$VERSION_FILE: __version__ is now $V"

# Note, the $VERSION_FILE has been 'suspended in time' with:
#   git update-index --assume-unchanged
##
cat << EOF > $VERSION_FILE
# Last modified: $(date)
##
# the TDT version
__version__ = '$V'
EOF

echo "Version updated!"
