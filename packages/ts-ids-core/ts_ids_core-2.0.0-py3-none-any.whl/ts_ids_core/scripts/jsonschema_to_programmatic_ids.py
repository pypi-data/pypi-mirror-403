import pathlib
from textwrap import dedent
from typing import Optional

import click
from typing_extensions import Literal


def import_schema_cmd(func):
    """
    Reusable command for schema importing to be used as a decorator.

    Example:

        @import_schema_cmd
        def my_func(*args, **kwargs):
            ...
    """

    @click.command(
        help="Create a programmatic IDS (PIDS) from a JSON file or IDS JSON Schema.",
    )
    @click.option(
        "--input",
        "-i",
        "input_",
        help=dedent(
            """
            The file from which to generate the programmatic IDS (PIDS). This may be sample
            data in JSON format or IDS JSON Schema. Use the `input-file-type` argument
            to specify whether it's JSON Schema or JSON data.
            """
        ),
        type=click.Path(
            file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path
        ),
        required=True,
    )
    @click.option(
        "--outfile",
        "-o",
        help=dedent(
            """
            The file to write the output to. If no value is supplied, the output file will
            be located in the same directory as the input JSON file and named after the JSON
            file. For example, if the input file is "/a/b/c.json" the output file will
            be "/a/b/c.py".
            """
        ),
        type=click.Path(
            file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path
        ),
        default=None,
        show_default=False,
    )
    @click.option(
        "--input-file-type",
        help=dedent(
            """
            The type of file being converted to PIDS, either 'jsonschema' or 'json'.
            'jsonschema' indicates the file is JSON Schema v7 (IDS Schema); 'json' indicates
            that the input file is sample data.
            """
        ).strip(),
        default="jsonschema",
        show_default=True,
        type=click.Choice(["json", "jsonschema"], case_sensitive=False),
    )
    @click.option(
        "--python",
        "-p",
        "target_python_version",
        help="The version of Python the generated code is expected to use.",
        type=click.Choice(["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]),
        default="3.11",
        show_default=True,
    )
    def import_schema(*args, **kwargs):
        return func(*args, **kwargs)

    return import_schema


def main(
    input_: pathlib.Path,
    outfile: Optional[pathlib.Path] = None,
    input_file_type: Literal["json", "jsonschema"] = "jsonschema",
    target_python_version: Literal[
        "3.8", "3.9", "3.10", "3.11", "3.12", "3.13"
    ] = "3.11",
) -> None:  # pragma: no cover
    """
    See documentation by running
    ``import-schema --help``.
    """
    # Imports not in module scope to allow direct importing and avoid lazy loading of
    # import_schema when adding to the ts_ids group in the cli module
    from datamodel_code_generator import (
        DataModelType,
        InputFileType,
        PythonVersion,
        generate,
    )

    input_abs_path = pathlib.Path(input_).absolute()
    if not input_abs_path.exists():
        raise FileNotFoundError(
            f"The input file, {str(input_abs_path)}, does not exist."
        )

    if outfile is None:
        to_dir = input_abs_path.parent
        outfile = to_dir.joinpath(f"{input_abs_path.stem}.py")

    outfile = pathlib.Path(outfile).absolute()
    generate(
        input_,
        input_file_type=InputFileType(input_file_type),
        output=outfile,
        output_model_type=DataModelType.PydanticV2BaseModel,
        strip_default_none=True,
        use_generic_container_types=True,
        reuse_model=True,
        snake_case_field=True,
        disable_appending_item_suffix=True,
        target_python_version=PythonVersion(target_python_version),
        use_schema_description=True,
        base_class="ts_ids_core.base.ids_element.IdsElement",
        class_name="TopLevelSchema",
        validation=False,
        use_double_quotes=True,
        custom_template_dir=pathlib.Path(__file__).parent.joinpath("_templates"),
        custom_file_header="# Generated using `import-schema` from `ts-ids-core`",
        additional_imports=[
            "ts_ids_core.annotations.Nullable",
            "ts_ids_core.annotations.NullableString",
            "ts_ids_core.annotations.NullableNumber",
            "ts_ids_core.annotations.NullableBoolean",
            "ts_ids_core.annotations.Required",
            "ts_ids_core.base.ids_field.IdsField",
        ],
        use_default_kwarg=True,
        field_include_all_keys=True,
        remove_special_field_name_prefix=True,
    )


@import_schema_cmd
def import_schema(*args, **kwargs) -> None:
    """
    See documentation by running
    ``import-schema --help``.
    """
    main(*args, **kwargs)


if __name__ == "__main__":
    import_schema()
