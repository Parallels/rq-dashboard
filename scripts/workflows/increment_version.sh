#!/bin/bash

VERSION=$(cat version.json | jq -r '.version')

MAJOR=$(echo $VERSION | cut -d. -f1) 
MINOR=$(echo $VERSION | cut -d. -f2)
PATCH=$(echo $VERSION | cut -d. -f3)

if [ "$1" == "major" ]; then
  MAJOR=$((MAJOR+1))
  MINOR=0
  PATCH=0
elif [ "$1" == "minor" ]; then
  MINOR=$((MINOR+1))
  PATCH=0
elif [ "$1" == "patch" ]; then
  PATCH=$((PATCH+1))
else
  echo "Invalid version type. Use 'major', 'minor' or 'patch'"
  exit 1
fi

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo $NEW_VERSION 