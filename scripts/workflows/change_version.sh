#!/bin/bash

# Get the filepath and version number from the arguments
filepath=$1
new_version=$2

# Get the current version number
current_version=$(cat $filepath | grep -oE 'VERSION = "[0-9]+\.[0-9]+\.[0-9]+' | cut -d'"' -f2)

# Replace the old version number with the new one
sed -i'' -e  "s/$current_version/$new_version/g"  "$filepath"

echo "Version number updated from $current_version to $new_version in $filepath"
