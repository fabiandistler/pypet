## ADDED Requirements

### Requirement: Improved parameter placeholder syntax
The system SHALL use `{{param}}` as the standard parameter placeholder syntax to avoid shell brace expansion conflicts.

#### Scenario: Use new parameter syntax
The system SHALL accept `{{param}}` syntax for parameter placeholders in commands.

#### Scenario: Reject old syntax with warning
The system SHALL reject `{param}` syntax and provide a warning about the new syntax.

#### Scenario: Shell compatibility
The system SHALL ensure parameter syntax is compatible with common shell environments.

### Requirement: Parameter validation and error handling
The system SHALL validate parameter definitions and provide clear error messages.

#### Scenario: Validate parameter names
The system SHALL reject parameter names containing invalid characters or empty names.

#### Scenario: Detect duplicate parameters
The system SHALL identify and report duplicate parameter names in the same command.

#### Scenario: Provide helpful error messages
The system SHALL provide specific, actionable error messages for parameter syntax issues.

### Requirement: Parameter metadata support
The system SHALL support storing parameter descriptions and default values.

#### Scenario: Store parameter descriptions
The system SHALL store descriptions for parameters in the snippet metadata.

#### Scenario: Store default values
The system SHALL store default values for parameters that can be used when no value is provided.

#### Scenario: Display parameter help
The system SHALL display parameter descriptions when prompting for values.

### Requirement: Shell alias generation compatibility
The system SHALL generate shell aliases that correctly handle the new parameter syntax.

#### Scenario: Generate compatible aliases
The system SHALL generate shell aliases that work with the `{{param}}` syntax.

#### Scenario: Handle parameter quoting in aliases
The system SHALL properly quote parameter values in generated shell aliases.

#### Scenario: Test alias functionality
The system SHALL verify that generated aliases work correctly in common shell environments.