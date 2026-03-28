#!/usr/bin/env bash
set -e

BUMP_TYPE="${1:-patch}"
DRY_RUN=false
NO_PUSH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-push)
            NO_PUSH=true
            shift
            ;;
        *)
            BUMP_TYPE="$1"
            shift
            ;;
    esac
done

if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo "Error: BUMP_TYPE must be major, minor, or patch"
    echo "Usage: $0 [major|minor|patch] [--dry-run] [--no-push]"
    exit 1
fi

if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "Error: uncommitted changes present"
    exit 1
fi

echo "=== Dry Run Preview ==="
uv version --bump "$BUMP_TYPE" --dry-run

if [[ "$DRY_RUN" == "true" ]]; then
    echo "(dry-run complete, no changes made)"
    exit 0
fi

CURRENT_BRANCH=$(git branch --show-current)
if [[ -z "$CURRENT_BRANCH" ]]; then
    echo "Error: release requires a checked-out branch"
    exit 1
fi

echo "=== Bumping version ==="
uv version --bump "$BUMP_TYPE"
NEW_VERSION=$(uv version --short)
echo "New version: $NEW_VERSION"

echo "=== Committing changes ==="
git add pyproject.toml uv.lock
git commit -m "bump version to $NEW_VERSION"

echo "=== Tagging ==="
git tag -a "v$NEW_VERSION" -m "v$NEW_VERSION"

if [[ "$NO_PUSH" == "false" ]]; then
    echo "=== Pushing ==="
    git push origin "$CURRENT_BRANCH" "v$NEW_VERSION"
    echo "Released v$NEW_VERSION"
else
    echo "Skipped push (--no-push flag)"
    echo "To push manually: git push origin $CURRENT_BRANCH && git push origin v$NEW_VERSION"
fi
