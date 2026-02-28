## ADDED Requirements

### Requirement: Interactive parameter prompting during snippet creation
The system SHALL prompt users for parameter values interactively when creating snippets that contain parameters.

#### Scenario: User creates snippet with parameters
- **WHEN** user runs `pypet snippet create` with a command containing parameters
- **THEN** system prompts for each parameter value with descriptive labels
- **AND** system validates parameter values before saving the snippet

#### Scenario: Parameter value validation
The system SHALL validate parameter values against basic constraints during interactive prompting.

#### Scenario: Skip prompting for optional parameters
The system SHALL allow users to skip optional parameter prompts during snippet creation.

### Requirement: Smart parameter detection from command strings
The system SHALL automatically detect parameter placeholders in command strings using the `{{param}}` syntax.

#### Scenario: Detect single parameter
The system SHALL identify a single parameter placeholder in a command string.

#### Scenario: Detect multiple parameters
The system SHALL identify multiple parameter placeholders in a command string.

#### Scenario: Detect parameters with special characters
The system SHALL correctly identify parameters containing underscores, numbers, and hyphens.

### Requirement: Improved parameter syntax validation
The system SHALL validate parameter syntax during snippet creation and provide helpful error messages.

#### Scenario: Invalid parameter syntax
The system SHALL detect and report invalid parameter syntax with specific error messages.

#### Scenario: Empty parameter names
The system SHALL reject parameter placeholders with empty names.

#### Scenario: Duplicate parameter names
The system SHALL detect and report duplicate parameter names in the same command.

### Requirement: Enhanced parameter editing interface
The system SHALL provide an improved interface for editing existing snippet parameters.

#### Scenario: Edit parameter values
The system SHALL allow users to modify parameter values in existing snippets.

#### Scenario: Add new parameters to existing snippets
The system SHALL support adding new parameters to existing snippets with interactive prompts.

#### Scenario: Remove parameters from existing snippets
The system SHALL support removing parameters from existing snippets with confirmation.