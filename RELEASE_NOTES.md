## ⚠️ BREAKING CHANGES

- **Parameter placeholder syntax changed from `{param}` to `{{param}}`**  
  - Reason: Old syntax conflicts with shell brace expansion  
  - Migration: Automatic migration on first use, or run `pypet migrate`  
  - See MIGRATION_GUIDE.md for detailed instructions

## ✨ Key Features

### Enhanced Parameter System

- **New `{{param}}` syntax** - Avoids shell brace expansion conflicts
- **Interactive parameter prompting** - Automatically detects and prompts for parameters during snippet creation
- **Smart parameter detection** - Automatically discovers parameters from command strings
- **Parameter metadata support** - Add descriptions and default values to parameters
- **Migration utilities** - Automatic and manual migration from old `{param}` syntax
  - `pypet migrate` - Migrate all snippets interactively
  - Automatic backup creation before migration
  - Batch migration with dry-run capability
- **New parameters module** (`pypet/parameters.py`)
- **New CLI parameters module** (`pypet/cli_parameters.py`)

## 🔧 Technical Improvements

- **Comprehensive parameter testing** - 26+ tests for parameter functionality
- **Enhanced Snippet model** - Integrated with new parameter system
- **Migration safety** - Automatic backups before any modifications
- **Better error messages** - Clear guidance for invalid parameters
- **Total test count: 180+ tests**

## 📚 Documentation

- **Migration Guide** - Step-by-step instructions for upgrading
- **Parameter examples** - Multiple examples of new syntax
- **Troubleshooting section** - Common issues and solutions

For full details, see CHANGELOG.md