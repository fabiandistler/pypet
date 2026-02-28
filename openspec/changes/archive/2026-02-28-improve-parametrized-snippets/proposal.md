## Why

Parametrized snippets in pypet are powerful but currently require users to manually format commands with placeholders and understand the parameter syntax. This creates a steep learning curve and makes the CLI less intuitive for new users. Improving the user experience around parametrized snippets will make pypet more accessible and reduce friction in creating and using parameterized commands.

## What Changes

- Add interactive parameter prompting when creating snippets with parameters
- Implement smart parameter detection from command strings with improved placeholder syntax
- Create a more intuitive parameter editing interface in the CLI
- Add validation and helpful error messages for parameter definitions
- **BREAKING**: Change the parameter placeholder syntax from `{param}` to `{{param}}` to avoid conflicts with shell brace expansion

## Capabilities

### New Capabilities

- `interactive-parameter-prompting`: Interactive CLI for parameter input during snippet creation
- `smart-parameter-detection`: Automatic parameter discovery from command strings
- `intuitive-parameter-syntax`: Improved placeholder syntax and validation
- `enhanced-cli-interface`: Better parameter editing and management in CLI

### Modified Capabilities

- `snippet-management`: Update parameter handling in existing snippet operations
- `cli-user-experience`: Enhance parameter-related CLI interactions

## Impact

- CLI command structure will change to support interactive parameter workflows
- Parameter storage format in TOML files will be updated to support new syntax
- Existing snippets using `{param}` syntax will need migration to `{{param}}`
- Shell alias generation will need updates to handle the new parameter format
