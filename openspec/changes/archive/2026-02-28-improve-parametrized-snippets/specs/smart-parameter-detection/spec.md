## ADDED Requirements

### Requirement: Smart parameter detection from command strings
The system SHALL automatically detect parameter placeholders in command strings using the `{{param}}` syntax.

#### Scenario: Detect single parameter
The system SHALL identify a single parameter placeholder in a command string.

#### Scenario: Detect multiple parameters
The system SHALL identify multiple parameter placeholders in a command string.

#### Scenario: Detect parameters with special characters
The system SHALL correctly identify parameters containing underscores, numbers, and hyphens.

#### Scenario: Handle nested parameter syntax
The system SHALL correctly handle parameter placeholders that contain special characters.

### Requirement: Parameter syntax validation and error reporting
The system SHALL validate parameter syntax during snippet creation and provide helpful error messages.

#### Scenario: Invalid parameter syntax
The system SHALL detect and report invalid parameter syntax with specific error messages.

#### Scenario: Empty parameter names
The system SHALL reject parameter placeholders with empty names.

#### Scenario: Duplicate parameter names
The system SHALL detect and report duplicate parameter names in the same command.

#### Scenario: Invalid characters in parameter names
The system SHALL reject parameter names containing invalid characters (spaces, special symbols).

### Requirement: Parameter metadata support
The system SHALL support parameter descriptions, default values, and validation rules.

#### Scenario: Add parameter descriptions
The system SHALL allow users to provide descriptions for parameters during snippet creation.

#### Scenario: Set default parameter values
The system SHALL support default values for parameters that users can override.

#### Scenario: Parameter validation rules
The system SHALL support basic validation rules for parameter values (e.g., required, format).

### Requirement: Migration from old syntax
The system SHALL provide migration support for existing snippets using `{param}` syntax.

#### Scenario: Detect old syntax in existing snippets
The system SHALL identify snippets using the deprecated `{param}` syntax.

#### Scenario: Migrate old syntax to new syntax
The system SHALL automatically migrate old syntax to new `{{param}}` syntax when updating snippets.

#### Scenario: Warn users about deprecated syntax
The system SHALL warn users when using deprecated syntax and suggest migration.