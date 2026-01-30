#!/bin/bash

# Project tree showing all git-tracked files + .env files

echo "📁 Project Tree"
echo "==============="

# Get all git tracked files and any .env files, sort and display as tree
{
    git ls-files 2>/dev/null
    find . -name ".env*" -type f 2>/dev/null | sed 's|^\./||'
} | sort -u | while read -r file; do
    # Calculate depth and create tree-like indentation
    depth=$(echo "$file" | tr -cd '/' | wc -c)
    indent=""
    for ((i=0; i<depth; i++)); do
        indent="│   $indent"
    done
    basename=$(basename "$file")
    echo "${indent}├── $basename"
done

echo ""
echo "Legend: Includes git-tracked files + .env* files"
