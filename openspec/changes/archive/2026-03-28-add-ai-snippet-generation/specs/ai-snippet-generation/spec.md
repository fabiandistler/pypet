## ADDED Requirements

### Requirement: Configure AI Provider

The system SHALL allow users to configure an OpenRouter API key and preferred model via the config file or environment variables (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`).

#### Scenario: Missing API Key

- **WHEN** the user runs `pypet gen` without an API key configured
- **THEN** the system prompts the user to enter their API key and saves it to the config file

#### Scenario: Existing API Key

- **WHEN** the user runs `pypet gen` with an API key already configured
- **THEN** the system bypasses the API key prompt and proceeds to generation

#### Scenario: Existing API Key From Environment

- **WHEN** the user runs `pypet gen` with `OPENROUTER_API_KEY` set and no API key in config
- **THEN** the system bypasses the API key prompt and proceeds to generation

#### Scenario: Model Selected From Environment

- **WHEN** the user runs `pypet gen` with `OPENROUTER_MODEL` set
- **THEN** the system uses the environment-provided model for generation

### Requirement: Generate Snippet

The system SHALL generate a shell snippet using an external AI provider based on a natural language prompt, returning structured JSON that maps to the Snippet model.

#### Scenario: Successful Generation

- **WHEN** the user provides a valid prompt like "kill process by port"
- **THEN** the system fetches a generated command, description, tags, and parameters, and displays them in a rich table

### Requirement: Interactive Save

The system SHALL prompt the user to save the generated snippet to their storage and optionally create an alias for it.

#### Scenario: User saves snippet

- **WHEN** the user is presented with the generated snippet
- **THEN** the system asks "Save this snippet? [Y/n]" and if confirmed, prompts for an optional alias, then saves the snippet using the existing storage mechanism.
