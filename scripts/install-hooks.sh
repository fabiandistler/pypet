#!/bin/bash

# Install Git hooks for pypet development
# Run this script to set up pre-push linting hooks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔧 Installing Git hooks for pypet development..."
echo ""

# Check if we're in a git repository
if [ ! -d "$REPO_ROOT/.git" ]; then
    print_error "This script must be run from within the pypet git repository"
    exit 1
fi

# Create pre-push hook
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash

# Pre-push hook for pypet
# Runs linting checks before pushing to prevent CI failures

echo "🔍 Running pre-push linting checks..."

# Check if we're in a git repository and have the right tools
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv to run linting checks."
    echo "   Visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if there are any Python files to lint
if ! find pypet tests -name "*.py" -type f | head -1 | grep -q .; then
    print_warning "No Python files found to lint"
    exit 0
fi

# Run Black formatting check
print_status "Running Black formatter check..."
if ! uv run python -m black --check pypet tests; then
    print_error "Black formatting check failed!"
    print_warning "Run 'uv run python -m black pypet tests' to fix formatting"
    exit 1
else
    print_success "Black formatting check passed ✨"
fi

# Run Ruff linting check
print_status "Running Ruff linting check..."
if ! uv run python -m ruff check pypet tests; then
    print_error "Ruff linting check failed!"
    print_warning "Run 'uv run python -m ruff check pypet tests --fix' to auto-fix issues"
    exit 1
else
    print_success "Ruff linting check passed 🎯"
fi

# Run type checking if mypy is available (optional)
if uv run python -c "import mypy" 2>/dev/null; then
    print_status "Running mypy type checking..."
    if ! uv run python -m mypy pypet --ignore-missing-imports 2>/dev/null; then
        print_warning "Type checking found issues (not blocking push)"
    else
        print_success "Type checking passed 🎯"
    fi
fi

# Run tests (can be disabled by setting SKIP_TESTS=1)
if [ "$SKIP_TESTS" != "1" ]; then
    print_status "Running quick test check..."
    if ! uv run python -m pytest tests/ -x --tb=short -q; then
        print_error "Tests failed!"
        print_warning "Fix failing tests before pushing, or set SKIP_TESTS=1 to bypass"
        exit 1
    else
        print_success "Tests passed ✅"
    fi
else
    print_warning "Tests skipped (SKIP_TESTS=1)"
fi

print_success "All pre-push checks passed! 🚀 Ready to push."
echo ""
EOF

# Make the hook executable
chmod +x "$HOOKS_DIR/pre-push"

print_success "Pre-push hook installed successfully!"
echo ""
echo "The hook will now run before every 'git push' and check:"
echo "  ✅ Black code formatting"
echo "  ✅ Ruff linting"
echo "  ✅ Tests (can be skipped with SKIP_TESTS=1)"
echo ""
echo "To bypass the hook temporarily, use: git push --no-verify"
echo "To skip tests permanently, add 'export SKIP_TESTS=1' to your shell profile"
echo ""
print_success "Happy coding! 🎉"