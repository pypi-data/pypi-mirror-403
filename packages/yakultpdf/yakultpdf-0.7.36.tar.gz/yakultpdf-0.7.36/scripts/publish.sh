#!/bin/bash
set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Publish Process...${NC}"

# 1. Check Directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: pyproject.toml not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Load .env if exists
if [ -f ".env" ]; then
    echo -e "${GREEN}📄 Loading environment from .env...${NC}"
    set -o allexport
    source .env
    set +o allexport
fi

# 2. Clean
echo -e "${GREEN}🧹 Cleaning previous build...${NC}"
rm -rf dist/

# 3. Build
echo -e "${GREEN}📦 Building...${NC}"
uv build

# 4. Confirmation
echo -e "${YELLOW}⚠️  Ready to publish to PyPI.${NC}"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}❌ Publish cancelled.${NC}"
    exit 1
fi

# 5. Publish
# 5. Publish
echo -e "${GREEN}📤 Publishing to PyPI...${NC}"

# Check for token in env or prompt
if [ -z "$UV_PUBLISH_TOKEN" ]; then
    echo -e "${YELLOW}🔑 Enter PyPI API Token (starts with pypi-):${NC}"
    read -s UV_PUBLISH_TOKEN
    echo
fi

if [ -z "$UV_PUBLISH_TOKEN" ]; then
    echo -e "${RED}❌ Error: No token provided.${NC}"
    exit 1
fi

uv publish --token "$UV_PUBLISH_TOKEN"

echo -e "${GREEN}✅ Done!${NC}"
