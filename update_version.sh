#!/usr/bin/env bash
# A simple script to update version tags, and update the version in static/index.html

usage() {
  echo "Usage: $0 [major|minor|patch]"
  echo "Defaults to 'patch'"
}

if [[ $# > 1 || $1 == "-h" || $1 == "--help" ]]; then
  usage
  exit 1
fi

if [[ $# == 1 ]]; then
  case $1 in
    major)
      mode="major"
      ;;
    minor)
      mode="minor"
      ;;
    patch)
      mode="patch"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
else
  mode="patch"
fi

# Only do this on a clean commit:
if ! git status | grep "working directory clean" > /dev/null 2>&1; then
  echo "Error: git repo not clean:"
  git status
  exit 1
fi

# Get current version:
current="$(git describe --tags --abbrev=0)"

# Split -- we assume version tags are of the form "v.X.Y.Z":
current_split=(${current//./ })
major=${current_split[1]}
minor=${current_split[2]}
patch=${current_split[3]}

echo "Current version: $major.$minor.$patch"

case $mode in
  major)
    major=$(( $major + 1 ))
    minor=0
    patch=0
    ;;
  minor)
    minor=$(( $minor + 1 ))
    patch=0
    ;;
  patch)
    patch=$(( $patch + 1 ))
    ;;
esac

echo "    New version: $major.$minor.$patch"
echo
read -p "Looks good? y/n: " -n1 response
echo

if [[ $response == 'y' || $response == "Y" ]]; then
  # Sanity checks, before we do anything:

  # OS X doesn't use GNU sed; to simplify the sed, below, we require gnu sed.
  # 'brew install gnu-sed' if it isn't installed on your system.
  if [[ "$(uname -s)" == "Darwin" ]]; then
    SED='gsed'
    if ! which gsed >/dev/null 2>&1; then
      echo "Error: GNU sed required on OS X. Install via 'brew install gnu-sed'."
      exit 1
    fi
  else
    SED='sed'
  fi

  # Verify we're running this from the right place - we could find this
  # automatically by tracking from .git, but meh
  INDEX_HTML="./roboviva/static/index.html"
  if [[ ! -e $INDEX_HTML ]]; then
    echo -n "Error: can't find index.html at $INDEX_HTML;"
    echo "are you running from the root level of the repo?"
    exit 1
  fi

  # Sanity checks done. Do it!
  #
  # Since I want the version + commit in the index.html, this creates a new
  # commit, simply to document the new version.

  # Update version in HTML:
  commit="$(git rev-parse --short=4 HEAD)"

  echo "Updating index.html..."
  $SED -i -e "
    /AUTO_VERSION/,/END_AUTO_VERSION/ {
      /AUTO_VERSION/n # Skip start line
      /END_AUTO_VERSION/ !{
      s/\( \+ \)version .*/\1version $major.$minor.$patch (commit $commit)/g
      }
    }" $INDEX_HTML


  echo "Making version commit + tag..."
  if ! git add $INDEX_HTML >/dev/null; then
    echo "Error adding changes, aborting."
    exit 1
  fi

  if ! git commit -m "New version: $major.$minor.$patch" >/dev/null; then
    echo "Error making version commit; aborting."
    exit 1
  fi
  if ! git tag "v.$major.$minor.$patch" > /dev/null; then
    echo "Error making tag -- undoing last commit via a non-hard reset."
    git reset HEAD^
    echo "Done -- note the index.html file will be dirty."
    exit 1
  fi

  echo "Done"

else
  echo "Aborting."
fi

