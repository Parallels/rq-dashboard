#!/bin/bash
# this script is used to generate release notes for a given release
# first argument is the pull request id for the last release
# the second is the new release number

# the script then grabs every pull request merged since that pull request
# and outputs a string of release notes

echo "Generating release notes for $2"

# get the last release pull request id
LAST_RELEASE_PR=$1

# get the new release number
NEW_RELEASE=$2

#get when the last release was merged
LAST_RELEASE_MERGED_AT=$(gh pr view $LAST_RELEASE_PR --repo Parallels/rq-dashboard --json mergedAt | jq -r '.mergedAt')

CHANGELIST=$(gh pr list --repo Parallels/rq-dashboard --base main --state merged --json title --search "merged:>$LAST_RELEASE_MERGED_AT -label:no-release")

# store the release notes in a variable so we can use it later

echo "Release $NEW_RELEASE" >>releasenotes.md

echo $CHANGELIST | jq -r '.[].title' | while read line; do
  echo " - $line" >>releasenotes.md
done

echo " "