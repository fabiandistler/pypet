"""
Interactive CLI utilities for parameter handling.
"""


import click

from .parameters import ParameterDetector, ParameterMetadata, ParameterValidator


class InteractiveParameterPrompt:
    """Provides interactive prompting for parameters in CLI."""

    @staticmethod
    def prompt_for_parameters(
        command: str, existing_params: dict[str, ParameterMetadata] | None = None
    ) -> dict[str, ParameterMetadata]:
        """
        Interactively prompt user for parameter definitions.

        Args:
            command: The command string containing parameter placeholders
            existing_params: Optional dict of already-defined parameters

        Returns:
            Dictionary of ParameterMetadata objects
        """
        existing_params = existing_params or {}

        try:
            detected_params = ParameterDetector.detect_parameters_new_syntax(command)
        except ValueError as e:
            click.echo(f"Error in command: {e}", err=True)
            raise

        all_params = {**existing_params, **detected_params}

        if not all_params:
            return {}

        click.echo("\nParameters detected in command:")
        click.echo("-" * 50)

        for param_name, param in all_params.items():
            click.echo(f"\nParameter: {param_name}")

            if param_name in existing_params:
                click.echo("  (Already defined)")
                continue

            if param.default is not None:
                click.echo(f"  Default value: {param.default}")

            description = click.prompt(
                "  Description (optional)",
                default="",
                show_default=False,
                type=str,
            )

            if description:
                param.description = description

            if param.default is None:
                add_default = click.confirm("Add a default value?", default=False)
                if add_default:
                    default = click.prompt("  Default value", type=str)
                    param.default = default

        return all_params

    @staticmethod
    def prompt_for_parameter_values(
        params: dict[str, ParameterMetadata],
    ) -> dict[str, str]:
        """
        Prompt user for parameter values.

        Args:
            params: Dictionary of ParameterMetadata objects

        Returns:
            Dictionary mapping parameter names to user-provided values
        """
        values = {}

        if not params:
            return values

        click.echo("\nEnter parameter values:")
        click.echo("-" * 50)

        for param_name, param in params.items():
            message = f"{param_name}"
            if param.description:
                message += f" ({param.description})"

            if param.default is not None:
                value = click.prompt(
                    message,
                    default=param.default,
                    type=str,
                )
            else:
                value = click.prompt(
                    message,
                    type=str,
                )

            values[param_name] = value

        return values

    @staticmethod
    def confirm_parameters(params: dict[str, ParameterMetadata]) -> bool:
        """
        Display parameters and ask user for confirmation.

        Returns:
            True if user confirms, False otherwise
        """
        if not params:
            return True

        click.echo("\nParameters:")
        for name, param in params.items():
            default_str = f" (default: {param.default})" if param.default else ""
            desc_str = f" - {param.description}" if param.description else ""
            click.echo(f"  • {name}{default_str}{desc_str}")

        return click.confirm("\nSave these parameters?", default=True)


class ParameterEditorCLI:
    """CLI interface for editing parameters."""

    @staticmethod
    def edit_parameters_prompt(
        existing_params: dict[str, ParameterMetadata],
    ) -> dict[str, ParameterMetadata]:
        """
        Interactively edit existing parameters.

        Returns:
            Updated parameters dictionary
        """
        updated_params = dict(existing_params)

        while True:
            click.echo("\nCurrent parameters:")
            if not updated_params:
                click.echo("  (None)")
            else:
                for i, (name, param) in enumerate(updated_params.items(), 1):
                    click.echo(
                        f"  {i}. {name}"
                        + (f" (default: {param.default})" if param.default else "")
                        + (f" - {param.description}" if param.description else "")
                    )

            action = click.prompt(
                "\nWhat would you like to do?",
                type=click.Choice(["add", "edit", "remove", "done"]),
            )

            if action == "done":
                break
            if action == "add":
                name = click.prompt("Parameter name")
                is_valid, error = ParameterValidator.validate_parameter_name(name)
                if not is_valid:
                    click.echo(f"Error: {error}", err=True)
                    continue

                if name in updated_params:
                    click.echo(f"Parameter '{name}' already exists", err=True)
                    continue

                description = click.prompt(
                    "Description (optional)", default="", show_default=False
                )
                add_default = click.confirm("Add a default value?", default=False)
                default = None
                if add_default:
                    default = click.prompt("Default value")

                updated_params[name] = ParameterMetadata(
                    name=name, default=default, description=description or None
                )
                click.echo(f"✓ Added parameter '{name}'")

            elif action == "edit":
                if not updated_params:
                    click.echo("No parameters to edit", err=True)
                    continue

                name = click.prompt(
                    "Parameter to edit",
                    type=click.Choice(list(updated_params.keys())),
                )
                param = updated_params[name]

                edit_description = click.confirm("Edit description?", default=False)
                if edit_description:
                    param.description = click.prompt(
                        "New description",
                        default=param.description or "",
                        show_default=True,
                    )

                edit_default = click.confirm("Edit default value?", default=False)
                if edit_default:
                    if param.default:
                        change_default = click.confirm(
                            "Clear default value?", default=False
                        )
                        if change_default:
                            param.default = None
                        else:
                            param.default = click.prompt(
                                "New default value",
                                default=param.default,
                                show_default=True,
                            )
                    else:
                        add_default = click.confirm(
                            "Add a default value?", default=False
                        )
                        if add_default:
                            param.default = click.prompt("Default value")

                click.echo(f"✓ Updated parameter '{name}'")

            elif action == "remove":
                if not updated_params:
                    click.echo("No parameters to remove", err=True)
                    continue

                name = click.prompt(
                    "Parameter to remove",
                    type=click.Choice(list(updated_params.keys())),
                )
                if click.confirm(f"Really remove '{name}'?", default=False):
                    del updated_params[name]
                    click.echo(f"✓ Removed parameter '{name}'")

        return updated_params
