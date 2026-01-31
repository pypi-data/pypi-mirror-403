#!/bin/bash
# Check Python version requirements of all dependencies

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if required tools are available
if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ Error: jq is not installed${NC}" >&2
    echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)" >&2
    exit 1
fi

# Read project's Python requirement from pyproject.toml
PROJECT_REQUIRES=$(grep '^requires-python' pyproject.toml | sed -E 's/.*"(.*)".*/\1/')
echo -e "${BLUE}📦 Project requires Python: ${PROJECT_REQUIRES}${NC}"
echo

# Get dependencies from pyproject.toml
# Find the dependencies array and extract package names
DEPENDENCIES=$(awk '
/^dependencies = \[/,/^\]$/ {
    if ($0 ~ /"[^"]+>=/ || $0 ~ /"[^"]+==/ || $0 ~ /"[^"]+",$/) {
        match($0, /"([^"]+)"/, arr)
        if (arr[1] != "") print arr[1]
    }
}' pyproject.toml)

if [ -z "$DEPENDENCIES" ]; then
    echo "No dependencies found"
    exit 0
fi

echo "Checking dependencies:"
echo "------------------------------------------------------------"

ALL_OK=true

while IFS= read -r dep; do
    # Skip empty lines
    [ -z "$dep" ] && continue

    # Extract package name (remove version specifiers)
    PACKAGE_NAME=$(echo "$dep" | sed -E 's/(>=|==|<|>|~=).*//' | xargs)

    # Fetch Python requirement from PyPI
    REQUIRES_PYTHON=$(curl -s "https://pypi.org/pypi/${PACKAGE_NAME}/json" 2>/dev/null | \
                      jq -r '.info.requires_python // "Not specified"' 2>/dev/null || echo "Not specified")

    if [ "$REQUIRES_PYTHON" = "Not specified" ]; then
        echo -e "${YELLOW}⚠${NC} ${dep:0:30}$(printf '%*s' $((30 - ${#dep})) '') (version not available)"
        ALL_OK=false
    else
        echo -e "${GREEN}✓${NC} ${dep:0:30}$(printf '%*s' $((30 - ${#dep})) '') requires Python ${REQUIRES_PYTHON}"
    fi
done <<< "$DEPENDENCIES"

echo "------------------------------------------------------------"
echo

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✓ All dependency version requirements checked!${NC}"
else
    echo -e "${YELLOW}⚠️  Some dependencies could not be checked${NC}"
    exit 1
fi
