#!/bin/bash
git config --global core.editor "vim"
git config --global push.default current
git config --global merge.conflictstyle diff3
git config --global user.name "Mark Pallone"
git config --global user.email "mark.c.pallone@gmail.com"
#                               ^ FILL THIS IN

# CLI tools
if command -v brew &> /dev/null; then
  brew install cloc
else
  echo "Error: Homebrew not found; cannot install cloc. Install brew first: https://brew.sh" >&2
fi

