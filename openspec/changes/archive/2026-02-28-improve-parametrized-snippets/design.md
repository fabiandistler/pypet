## Context

pypet currently supports parametrized snippets using a simple `{param}` placeholder syntax, but the user experience is limited. Users must manually format commands with placeholders, understand the parameter syntax, and there's no interactive guidance during snippet creation. The current implementation lacks validation, smart detection, and intuitive parameter management.

## Goals / Non-Goals

**Goals:**
- Make parametrized snippets more accessible to new users
- Reduce the learning curve for creating parameterized commands
- Provide interactive guidance during snippet creation
- Implement smart parameter detection from command strings
- Improve parameter syntax to avoid shell conflicts
- Add validation and helpful error messages

**Non-Goals:**
- Change the core snippet storage format beyond parameter syntax
- Add complex parameter types (arrays, objects, etc.)
- Implement advanced parameter validation rules
- Create a graphical user interface
- Support parameter dependencies or conditional parameters

## Decisions

**Decision 1**: Change parameter placeholder syntax from `{param}` to `{{param}}`
- **Why**: Avoid conflicts with shell brace expansion which causes unexpected behavior
- **Alternatives considered**: Escape braces, use different delimiters like `$param$`, keep current syntax with warnings
- **Rationale**: Double braces are clear, avoid shell conflicts, and are commonly used in template systems

**Decision 2**: Implement interactive parameter prompting during snippet creation
- **Why**: Guide users through parameter definition process and reduce errors
- **Alternatives considered**: Auto-detect parameters only, require manual parameter section, use configuration files
- **Rationale**: Interactive approach provides immediate feedback and educational value

**Decision 3**: Use Click's built-in prompting capabilities for parameter input
- **Why**: Leverage existing, well-tested library features
- **Alternatives considered**: Custom input handling, external prompt libraries, shell-based input
- **Rationale**: Click integration ensures consistency with existing CLI and reduces maintenance

**Decision 4**: Add smart parameter detection with validation
- **Why**: Reduce manual work and catch errors early
- **Alternatives considered**: Manual parameter definition only, simple pattern matching only
- **Rationale**: Balance between automation and user control with proper validation

## Risks / Trade-offs

**Breaking change to parameter syntax** → Provide migration tool and clear documentation
**CLI complexity increase** → Keep interactive prompts optional and maintain backward compatibility
**Performance impact on parameter detection** → Optimize regex patterns and cache results
**User confusion during transition** → Clear error messages and migration guidance