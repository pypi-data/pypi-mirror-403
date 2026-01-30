from typing import Callable

import click

from ts_ids_core.scripts._logging import get_warning_logger
from ts_ids_core.scripts.docs import docs
from ts_ids_core.scripts.jsonschema_to_programmatic_ids import (
    import_schema,
    import_schema_cmd,
)
from ts_ids_core.scripts.programmatic_ids_to_jsonschema import (
    export_schema,
    export_schema_cmd,
)

logger = get_warning_logger(name="cli")


def _check_code_gen_dependency() -> None:
    """
    Raise error if datamodel code gen is not installed
    raising here and not inside the jsonschema_to_programmatic_ids module will allow
    throwing the error without requiring a user to pass arguments to import-schema
    """
    try:
        import datamodel_code_generator  # noqa
    except ImportError as exception:
        raise ImportError(
            "The `import-schema` command requires additional dependencies to be installed. "
            'To install them, use `pip install "ts-ids-core[import-schema]"`, '
            'or `poetry add "ts-ids-core[import-schema]"`, or equivalent in other package '
            "managers. Importing from schema.json is a one-time task, so it's best to "
            "remove this optional extra dependency when done converting to "
            "programmatic IDS."
        ) from exception


def validate_code_gen_import(f: Callable) -> Callable:
    """
    A decorator for validating datamodel_code_generator is installed.
    This is intended to wrap a click.command to validate the import before
    click validates the passed arguments. This will allow the dependency check to be
    completed without requiring a user to pass arguments to import-schema.

    To ensure import validation is done before click argument validation, use this as the outermost
    decorator on the command. Example:

    @validate_code_gen_import
    @click.command(...)
    @click.option(...)
    def my_command()
        ...
    """

    def new_func(*args, **kwargs):
        _check_code_gen_dependency()
        return f(*args, **kwargs)

    return new_func


@click.group(
    help="ts-ids contains a group of commands and is not executable alone."
    " Instead, see the group's commands below and call as `ts-ids [command][options]`"
)
@click.pass_context
def ts_ids(ctx: click.Context) -> None:
    if ctx.invoked_subcommand == "import-schema":
        _check_code_gen_dependency()


ts_ids.add_command(import_schema)
ts_ids.add_command(export_schema)
ts_ids.add_command(docs)


def _warn_deprecation(cmd_name: str) -> None:
    logger.warning(
        f"The command '{cmd_name}' is deprecated and will be removed in a future release."
        f" Please use the ts-ids group command, 'ts-ids {cmd_name} [OPTIONS]'."
        " For more information, review the documentation locally by running 'ts-ids docs'"
    )


@validate_code_gen_import
@import_schema_cmd
@click.pass_context
def legacy_import(ctx: click.Context, *args, **kwargs) -> None:
    """
    Backwards compatible CLI command for import-schema which is outside of the ts-ids group.
    This can be called as `import-schema [OPTIONS]` without needing to specify the ts-ids group.
    This serves a similar functionality to the ts-ids group function as it validates the
    code gen import exists for invoking the import-schema command.

    :param ctx: Click context used for forwarding to
    :param args: args passed by user
    :param kwargs: kwargs passed by user
    """
    _warn_deprecation(ctx.command.name)
    ctx.forward(import_schema)


@export_schema_cmd
@click.pass_context
def legacy_export(ctx, *args, **kwargs) -> None:
    """
    Backwards compatible CLI command for export-schema which is outside of the ts-ids group.
    This can be called as `export-schema [OPTIONS]` without needing to specify the ts-ids group.
    Provides same functionality as `ts-ids export-schema` and logs deprecation warning.

    :param ctx: Click context used for forwarding to
    :param args: args passed by user
    :param kwargs: kwargs passed by user
    """
    _warn_deprecation(ctx.command.name)
    ctx.forward(export_schema)
