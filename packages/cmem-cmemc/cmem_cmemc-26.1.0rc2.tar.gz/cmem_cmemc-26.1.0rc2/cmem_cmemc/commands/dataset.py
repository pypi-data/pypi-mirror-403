"""dataset commands for cmem command line interface."""

import json

import click
import requests.exceptions
from click import Context, UsageError
from cmem.cmempy.config import get_cmem_base_uri
from cmem.cmempy.workspace import get_task_plugin_description, get_task_plugins
from cmem.cmempy.workspace.projects.datasets.dataset import (
    create_dataset,
    delete_dataset,
    get_dataset,
    post_resource,
    update_dataset,
)
from cmem.cmempy.workspace.projects.resources.resource import (
    get_resource_response,
)
from cmem.cmempy.workspace.search import list_items

from cmem_cmemc import completion
from cmem_cmemc.command import CmemcCommand
from cmem_cmemc.command_group import CmemcGroup
from cmem_cmemc.commands.file import _upload_file_resource, resource
from cmem_cmemc.completion import get_dataset_file_mapping
from cmem_cmemc.context import ApplicationContext, build_caption
from cmem_cmemc.exceptions import CmemcError
from cmem_cmemc.object_list import (
    DirectListPropertyFilter,
    DirectMultiValuePropertyFilter,
    DirectValuePropertyFilter,
    ObjectList,
    compare_regex,
    transform_extract_labels,
)
from cmem_cmemc.parameter_types.path import ClickSmartPath
from cmem_cmemc.smart_path import SmartPath as Path
from cmem_cmemc.string_processor import DatasetLink, DatasetTypeLink
from cmem_cmemc.title_helper import DatasetTypeTitleHelper, ProjectTitleHelper
from cmem_cmemc.utils import check_or_select_project, struct_to_table


def get_datasets(ctx: Context) -> list[dict]:
    """Get datasets for object list."""
    _ = ctx
    return list_items(item_type="dataset")["results"]  # type: ignore[no-any-return]


dataset_list = ObjectList(
    name="datasets",
    get_objects=get_datasets,
    filters=[
        DirectValuePropertyFilter(
            name="project",
            description="Filter by project ID.",
            property_key="projectId",
            completion_method="values",
            title_helper=ProjectTitleHelper(),
        ),
        DirectValuePropertyFilter(
            name="regex",
            description="Filter by regex matching the dataset label.",
            property_key="label",
            compare=compare_regex,
            completion_method="none",
        ),
        DirectValuePropertyFilter(
            name="type",
            description="Filter by dataset type.",
            property_key="pluginId",
            compare=compare_regex,
            completion_method="values",
            title_helper=DatasetTypeTitleHelper(),
        ),
        DirectListPropertyFilter(
            name="tag",
            description="Filter by tag label.",
            property_key="tags",
            transform=transform_extract_labels,
        ),
        DirectMultiValuePropertyFilter(
            name="ids",
            description="Internal filter for multiple dataset IDs.",
            property_key="id",
        ),
    ],
)


def _validate_and_split_dataset_id(dataset_id: str) -> tuple[str, str]:
    """Validate and split cmemc dataset ID.

    Args:
    ----
        dataset_id (str): The cmemc dataset ID in the workspace.

    Raises:
    ------
        ClickException: in case the dataset ID is not splittable

    """
    try:
        project_part = dataset_id.split(":")[0]
        dataset_part = dataset_id.split(":")[1]
    except IndexError as error:
        raise CmemcError(
            f"{dataset_id} is not a valid dataset ID. Use the "
            "'dataset list' command to get a list of existing datasets."
        ) from error
    return project_part, dataset_part


def _validate_dataset_ids(dataset_ids: tuple[str, ...]) -> None:
    """Validate that all provided dataset IDs exist."""
    if not dataset_ids:
        return
    all_datasets = list_items(item_type="dataset")["results"]
    all_dataset_ids = [_["projectId"] + ":" + _["id"] for _ in all_datasets]
    for dataset_id in dataset_ids:
        if dataset_id not in all_dataset_ids:
            raise CmemcError(
                f"Dataset {dataset_id} not available. Use the 'dataset list' "
                "command to get a list of existing datasets."
            )


def _get_datasets_to_delete(
    ctx: Context,
    dataset_ids: tuple[str, ...],
    all_: bool,
    filter_: tuple[tuple[str, str], ...],
) -> list[str]:
    """Get the list of dataset IDs to delete based on selection method."""
    if all_:
        # Get all datasets
        datasets = list_items(item_type="dataset")["results"]
        return [_["projectId"] + ":" + _["id"] for _ in datasets]

    # Validate provided IDs exist before proceeding
    _validate_dataset_ids(dataset_ids)

    # Build filter list
    filter_to_apply = list(filter_) if filter_ else []

    # Add IDs if provided (using internal multi-value filter)
    if dataset_ids:
        # Extract just the dataset ID part (after the colon) for filtering
        dataset_id_parts = [_.split(":")[1] for _ in dataset_ids]
        filter_to_apply.append(("ids", ",".join(dataset_id_parts)))

    # Apply filters
    datasets = dataset_list.apply_filters(ctx=ctx, filter_=filter_to_apply)

    # Build full dataset IDs
    result = [_["projectId"] + ":" + _["id"] for _ in datasets]

    # Validation: ensure we found datasets
    if not result and not dataset_ids:
        raise CmemcError("No datasets found matching the provided filters.")

    return result


def _post_file_resource(
    app: ApplicationContext,
    project_id: str,
    dataset_id: str,
    local_file_name: str,
) -> None:
    """Upload a local file as a dataset resource to a project.

    Args:
    ----
        app: the click cli app context.
        project_id: The project ID in the workspace.
        dataset_id: The dataset ID in the workspace.
        local_file_name: The path to the local file name

    Raises:
    ------
        ValueError: if resource exists and no replace

    """
    app.echo_info(
        f"Upload {local_file_name} as a file resource of dataset "
        f"{dataset_id} to project {project_id} ... ",
        nl=False,
    )
    post_resource(
        project_id=project_id,
        dataset_id=dataset_id,
        file_resource=ClickSmartPath.open(local_file_name),
    )
    app.echo_success("done")


def _get_metadata_out_of_parameter(parameter_dict: dict) -> dict:
    """Extract metadata keys out of the parameter dict.

    Args:
    ----
        parameter_dict (dict): the dictionary of given parameters.

    Returns:
    -------
        The dictionary of only the known metadata fields.

    """
    metadata_dict = {}
    if "label" in parameter_dict:
        metadata_dict["label"] = parameter_dict["label"]
    if "description" in parameter_dict:
        metadata_dict["description"] = parameter_dict["description"]
    return metadata_dict


def _get_read_only_out_of_parameter(parameter_dict: dict) -> bool:
    """Extract readonly key value out of the parameter dict.

    Args:
    ----
        parameter_dict (dict): the dictionary of given parameters.

    Returns:
    -------
        The value of read only field.

    """
    read_only = parameter_dict.get("readOnly", False)
    if read_only in ("true", True, "True"):
        return True
    if read_only in ("false", False, "False"):
        return False
    raise CmemcError(f"readOnly parameter should be 'true' or 'false' - was {read_only!r}")


def _extend_parameter_with_metadata(
    app: ApplicationContext,
    parameter_dict: dict,
    dataset_type: str,
    dataset_file: str,
) -> dict:
    """Extend the parameter with label if needed.

    Args:
    ----
        app: the click cli app context.
        parameter_dict: The dictionary of given dataset parameters
        dataset_type: The dataset type ID
        dataset_file: The path of the local file

    Returns:
    -------
        An extended parameter dictionary (label + file)

    """
    if "label" not in parameter_dict:
        label = f"Unnamed {dataset_type} dataset"
        if dataset_file:
            label = Path(dataset_file).name
        if "file" in parameter_dict:
            label = parameter_dict["file"]
        app.echo_warning(
            "Missing dataset label (-p label xxx) - " f"this generated label will be used: {label}"
        )
        parameter_dict["label"] = label
    return parameter_dict


def _check_or_set_dataset_type(
    app: ApplicationContext, parameter_dict: dict, dataset_type: str, dataset_file: str
) -> str:
    """Check for missing dataset type.

    Args:
    ----
        app: the click cli app context.
        parameter_dict: The dictionary of given dataset parameters
        dataset_type: The dataset type ID.
        dataset_file: The path of the local file.

    Returns:
    -------
        A dataset type based the given file names.

    """
    source = Path(dataset_file).name if dataset_file else ""
    target = parameter_dict.get("file", "")
    suggestions = [
        (extension, info["type"]) for extension, info in get_dataset_file_mapping().items()
    ]
    if not dataset_type:
        for check, type_ in suggestions:
            if source.endswith(check) or target.endswith(check):
                dataset_type = type_
                break
        if not dataset_type:
            raise UsageError("Missing parameter. Please specify a dataset " "type with '--type'.")
        app.echo_warning(
            "Missing dataset type (--type) - based on the used file name, "
            f"this type is assumed: {dataset_type}"
        )
    return dataset_type


def _show_parameter_list(app: ApplicationContext, dataset_type: str) -> None:
    """Output the parameter list for a given dataset type.

    Args:
    ----
        app: the click cli app context.
        dataset_type: The type from which the parameters are listed.

    """
    plugin = get_task_plugin_description(dataset_type)
    properties = plugin["properties"]
    required_properties = plugin["required"]
    table = []
    for key in properties:
        if key in required_properties:
            parameter = key + " *"
            description = "(Required) " + properties[key]["description"]
        else:
            parameter = key
            description = properties[key]["description"]
        row = [
            parameter,
            description,
        ]
        table.append(row)

    table = completion.add_read_only_and_uri_property_parameters(table)

    # metadata always on top, then sorted by key
    table = sorted(table, key=lambda k: k[0].lower())
    table = completion.add_metadata_parameter(table)
    app.echo_info_table(
        table,
        headers=["Parameter", "Description"],
        caption=build_caption(len(table), f"{dataset_type} dataset parameter"),
        empty_table_message="No parameters found for this dataset type.",
    )


def _show_type_list(app: ApplicationContext) -> None:
    """Output the list of dataset types.

    Args:
    ----
        app: the click cli app context.

    """
    plugins = get_task_plugins()
    table = []
    for plugin_id in plugins:
        plugin = plugins[plugin_id]
        if plugin["taskType"] == "Dataset":
            id_ = plugin_id
            title = plugin["title"]
            description = plugin["description"].partition("\n")[0]
            row = [
                id_,
                f"{title}: {description}",
            ]
            table.append(row)
    app.echo_info_table(
        table,
        headers=["Dataset Type", "Description"],
        sort_column=1,
        caption=build_caption(len(table), "dataset type"),
        empty_table_message="No dataset types found.",
    )


def _check_or_select_dataset_type(app: ApplicationContext, dataset_type: str) -> tuple[str, dict]:
    """Test type and return plugin.

    Args:
    ----
        app: the click cli app context.
        dataset_type: A dataset type

    Raises:
    ------
        CmemcError: If type is not known

    Returns:
    -------
        A tuple of dataset_type and corresponding plugin description (dict)

    """
    try:
        app.echo_debug(f"check type {dataset_type}")
        plugin = get_task_plugin_description(dataset_type)
    except requests.exceptions.HTTPError as error:
        raise CmemcError(f"Unknown dataset type: {dataset_type}.") from error
    else:
        return dataset_type, plugin


@click.command(cls=CmemcCommand, name="list")
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    multiple=True,
    shell_complete=dataset_list.complete_values,
    help=dataset_list.get_filter_help_text(),
)
@click.option(
    "--raw", is_flag=True, help="Outputs raw JSON objects of the dataset search API response."
)
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only dataset IDs and no labels or other metadata. "
    "This is useful for piping the IDs into other cmemc commands.",
)
@click.pass_context
def list_command(ctx: Context, filter_: tuple[tuple[str, str]], raw: bool, id_only: bool) -> None:
    """List available datasets.

    Output and filter a list of available datasets. Each dataset is listed
    with its ID, type and label.
    """
    app = ctx.obj
    datasets = dataset_list.apply_filters(ctx=ctx, filter_=filter_)

    if raw:
        app.echo_info_json(datasets)
    elif id_only:
        for _ in datasets:
            app.echo_info(_["projectId"] + ":" + _["id"])
    else:
        table = []
        for _ in datasets:
            # Build row with dataset ID; the Label column will be transformed by DatasetLink
            dataset_id = _["projectId"] + ":" + _["id"]
            row = [dataset_id, _["pluginId"], dataset_id]

            table.append(row)
        filtered = len(filter_) > 0
        app.echo_info_table(
            table,
            headers=["Dataset ID", "Type", "Label"],
            sort_column=2,
            cell_processing={2: DatasetLink(), 1: DatasetTypeLink()},
            caption=build_caption(len(table), "dataset", filtered=filtered),
            empty_table_message="No datasets found for these filters."
            if filtered
            else "No datasets found. Use the `dataset create` command to create a new dataset.",
        )


@click.command(cls=CmemcCommand, name="delete")
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Delete all datasets. " "This is a dangerous option, so use it with care.",
)
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    multiple=True,
    shell_complete=dataset_list.complete_values,
    help=dataset_list.get_filter_help_text(),
)
@click.argument("dataset_ids", nargs=-1, type=click.STRING, shell_complete=completion.dataset_ids)
@click.pass_context
def delete_command(
    ctx: Context,
    all_: bool,
    filter_: tuple[tuple[str, str]],
    dataset_ids: tuple[str],
) -> None:
    """Delete datasets.

    This command deletes existing datasets in integration projects from
    Corporate Memory. The corresponding dataset resources will not be deleted.

    Warning: Datasets will be deleted without prompting.

    Note: Datasets can be listed by using the `dataset list` command.
    """
    app = ctx.obj

    # Validation: require at least one selection method
    if not dataset_ids and not all_ and not filter_:
        raise UsageError(
            "Either specify at least one dataset ID"
            " or use a --filter option,"
            " or use the --all option to delete all datasets."
        )

    if dataset_ids and (all_ or filter_):
        raise UsageError("Either specify a dataset ID OR" " use a --filter or the --all option.")

    # Get datasets to delete based on selection method
    datasets_to_delete = _get_datasets_to_delete(ctx, dataset_ids, all_, filter_)

    # Avoid double removal as well as sort IDs
    processed_ids = sorted(set(datasets_to_delete), key=lambda v: v.lower())
    count = len(processed_ids)

    # Delete each dataset
    for current, dataset_id in enumerate(processed_ids, start=1):
        current_string = str(current).zfill(len(str(count)))
        app.echo_info(f"Delete dataset {current_string}/{count}: {dataset_id} ... ", nl=False)
        project_part, dataset_part = _validate_and_split_dataset_id(dataset_id)
        app.echo_debug(f"Project ID is {project_part}, dataset ID is {dataset_part}")
        delete_dataset(project_part, dataset_part)
        app.echo_success("deleted")


@click.command(cls=CmemcCommand, name="download")
@click.argument("dataset_id", type=click.STRING, shell_complete=completion.dataset_ids)
@click.argument(
    "output_path",
    required=True,
    type=ClickSmartPath(allow_dash=True, dir_okay=False, writable=True),
)
@click.option(
    "--replace",
    is_flag=True,
    help="Replace existing files. This is a dangerous option, " "so use it with care!",
)
@click.pass_obj
def download_command(
    app: ApplicationContext, dataset_id: str, output_path: str, replace: bool
) -> None:
    """Download the resource file of a dataset.

    This command downloads the file resource of a dataset to your local
    file system or to standard out (`-`).
    Note that this is not possible for dataset types such as
    Knowledge Graph (`eccencaDataplatform`) or SQL endpoint (`sqlEndpoint`).

    Without providing an output path, the output file name will be the
    same as the remote file resource.

    Note: Datasets can be listed by using the `dataset list` command.
    """
    app.echo_debug(
        f"Dataset ID is {dataset_id}; "
        f"output path is {click.format_filename(output_path)}. "
        f"replace is {replace}."
    )
    project_part, dataset_part = _validate_and_split_dataset_id(dataset_id)
    project = get_dataset(project_part, dataset_part)
    try:
        file = project["data"]["parameters"]["file"]
    except KeyError as no_file_resource:
        raise CmemcError(
            f"The dataset {dataset_id} has no associated file resource."
        ) from no_file_resource
    if Path(output_path).exists() and replace is not True:
        raise UsageError(
            f"Target file {click.format_filename(output_path)} already "
            "exists. Use --replace in case you want to replace it."
        )
    with get_resource_response(project_part, file) as response:
        # if piping file to stdout, no info messages
        if output_path != "-":
            app.echo_info(
                f"Download resource {file} of dataset {dataset_id} to file "
                f"{click.format_filename(output_path)} ... ",
                nl=False,
            )
        with click.open_file(output_path, "wb") as resource_file:
            for chunk in response.iter_content(chunk_size=8192):
                resource_file.write(chunk)
            # if piping file to stdout, no info messages
        if output_path != "-":
            app.echo_success("done")


@click.command(cls=CmemcCommand, name="upload")
@click.argument("dataset_id", type=click.STRING, shell_complete=completion.dataset_ids)
@click.argument(
    "input_path",
    required=True,
    shell_complete=completion.dataset_files,
    type=ClickSmartPath(allow_dash=True, dir_okay=False, writable=True, remote_okay=True),
)
@click.pass_obj
def upload_command(app: ApplicationContext, dataset_id: str, input_path: str) -> None:
    """Upload a resource file to a dataset.

    This command uploads a file to a dataset.
    The content of the uploaded file replaces the remote file resource.
    The name of the remote file resource will not be changed.

    Warning: If the remote file resource is used in more than one dataset,
    all of these datasets are affected by this command.

    Warning: The content of the uploaded file is not tested, so uploading
    a JSON file to an XML dataset will result in errors.

    Note: Datasets can be listed by using the `dataset list` command.

    Example: cmemc dataset upload cmem:my-dataset new-file.csv
    """
    project_part, dataset_part = _validate_and_split_dataset_id(dataset_id)

    _post_file_resource(
        app=app,
        project_id=project_part,
        dataset_id=dataset_part,
        local_file_name=input_path,
    )


@click.command(cls=CmemcCommand, name="inspect")
@click.argument("dataset_id", type=click.STRING, shell_complete=completion.dataset_ids)
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.pass_obj
def inspect_command(app: ApplicationContext, dataset_id: str, raw: bool) -> None:
    """Display metadata of a dataset.

    Note: Datasets can be listed by using the `dataset list` command.
    """
    app.echo_debug(f"Dataset ID is {dataset_id}")
    project_part, dataset_part = _validate_and_split_dataset_id(dataset_id)
    project = get_dataset(project_part, dataset_part)
    if raw:
        app.echo_info_json(project)
    else:
        table = struct_to_table(project)
        app.echo_info_table(table, headers=["Key", "Value"], sort_column=0)


@click.command(cls=CmemcCommand, name="create")
@click.argument(
    "DATASET_FILE",
    required=False,
    shell_complete=completion.dataset_files,
    type=ClickSmartPath(allow_dash=False, readable=True, exists=True, remote_okay=True),
)
@click.option(
    "--type",
    "-t",
    "dataset_type",
    multiple=False,
    type=click.STRING,
    shell_complete=completion.dataset_types,
    help="The dataset type of the dataset to create. Example types are 'csv',"
    "'json' and 'eccencaDataPlatform' (-> Knowledge Graph).",
)
@click.option(
    "--project",
    "project_id",
    type=click.STRING,
    shell_complete=completion.project_ids,
    help="The project, where you want to create the dataset in. If there is "
    "only one project in the workspace, this option can be omitted.",
)
@click.option(
    "--parameter",
    "-p",
    type=(str, str),
    shell_complete=completion.dataset_parameter,
    multiple=True,
    help="A set of key/value pairs. Each dataset type has different "
    "parameters (such as charset, arraySeparator, ignoreBadLines, ...). "
    "In order to get a list of possible parameter, use the"
    "'--help-parameter' option.",
)
@click.option(
    "--replace",
    is_flag=True,
    help="Replace remote file resources in case there " "already exists a file with the same name.",
)
@click.option(
    "--id",
    "dataset_id",
    type=click.STRING,
    help="The dataset ID of the dataset to create. "
    "The dataset ID will be automatically created in case it is not present.",
)
@click.option(
    "--help-types",
    is_flag=True,
    help="Lists all possible dataset types on given Corporate Memory instance. "
    "Note that this option already needs access to the instance.",
)
@click.option(
    "--help-parameter",
    is_flag=True,
    help="Lists all possible (optional and mandatory) parameter for a dataset "
    "type. Note that this option already needs access to the instance.",
)
@click.pass_obj
def create_command(  # noqa: PLR0913
    app: ApplicationContext,
    dataset_file: str,
    replace: bool,
    project_id: str,
    dataset_id: str,
    dataset_type: str,
    parameter: tuple[tuple[str, str]],
    help_parameter: bool,
    help_types: bool,
) -> None:
    """Create a dataset.

    Datasets are created in projects and can have associated file
    resources. Each dataset has a type (such as `csv`) and a list of
    parameters which can alter or specify the dataset behaviour.

    To get more information about available dataset types and associated
    parameters, use the --help-types and --help-parameter options.

    Example: cmemc dataset create --project my-project --type csv my-file.csv
    """
    if help_types:
        _show_type_list(app)
        return

    # transform the parameter list of tuple to a dictionary
    parameter_dict = dict(parameter)

    dataset_type = _check_or_set_dataset_type(
        app=app,
        parameter_dict=parameter_dict,
        dataset_type=dataset_type,
        dataset_file=dataset_file,
    )

    if help_parameter:
        _show_parameter_list(app, dataset_type=dataset_type)
        return

    dataset_type, plugin = _check_or_select_dataset_type(app, dataset_type)

    parameter_dict = _extend_parameter_with_metadata(
        app=app, parameter_dict=parameter_dict, dataset_type=dataset_type, dataset_file=dataset_file
    )

    project_id = check_or_select_project(app, project_id)

    # file required but not given
    if "file" in plugin["required"] and not dataset_file and "file" not in parameter_dict:
        raise UsageError(
            f"The dataset type {dataset_type} is file based, so you need "
            "to specify a file with the create command."
        )

    # file required and given
    # dataset_file = file path from the command line
    # parameter_dict["file"] = local name in DI
    if "file" in plugin["required"] and dataset_file:
        # add file parameter for the project if needed
        if "file" not in parameter_dict:
            parameter_dict["file"] = Path(dataset_file).name

        _upload_file_resource(
            app=app,
            project_id=project_id,
            local_file_name=dataset_file,
            remote_file_name=parameter_dict["file"],
            replace=replace,
        )

    # create dataset resource
    app.echo_info(f"Create a new dataset {project_id}:", nl=False)
    created_dataset = create_dataset(
        dataset_id=dataset_id,
        project_id=project_id,
        dataset_type=dataset_type,
        parameter=parameter_dict,
        metadata=_get_metadata_out_of_parameter(parameter_dict),
        read_only=_get_read_only_out_of_parameter(parameter_dict),
        uri_property=parameter_dict.get("uriProperty", ""),
    )
    returned_id = json.loads(created_dataset)["id"]
    app.echo_info(f"{returned_id} ... ", nl=False)
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="update")
@click.argument(
    "dataset_id",
    type=click.STRING,
    required=True,
    shell_complete=completion.dataset_ids,
)
@click.option(
    "--parameter",
    "-p",
    type=(str, str),
    shell_complete=completion.dataset_parameter,
    multiple=True,
    help="A configuration parameter key/value pair. Each dataset type has different "
    "parameters (such as charset, arraySeparator, ignoreBadLines, ...). "
    "In order to get a list of possible parameter, use the"
    "'--help-parameter' option.",
)
@click.option(
    "--help-parameter",
    is_flag=True,
    help="Lists all possible (optional and mandatory) configuration parameter for"
    " a given dataset. Note that this option already needs access to the instance.",
)
@click.pass_obj
def update_command(
    app: ApplicationContext,
    dataset_id: str,
    parameter: tuple[tuple[str, str]],
    help_parameter: bool,
) -> None:
    """Update a dataset.

    With this command, you can update the configuration of an existing dataset.
    Similar to the `dataset create` command, you need to use configuration key/value
    pairs on the `--parameter` option.

    To get more information about the available configuration parameters on a dataset,
    use the `--help-parameter` option.

    Example: cmemc dataset update my-project:my-csv -p separator ";"
    """
    project_part, dataset_part = _validate_and_split_dataset_id(dataset_id)
    project = get_dataset(project_part, dataset_part)
    dataset_type = project["data"]["type"]

    if help_parameter:
        _show_parameter_list(app, dataset_type=dataset_type)
        return

    if not parameter:
        raise UsageError(
            "You need to use the `--parameter/-p` option at least once,"
            " in order to execute this command."
        )

    desc = get_task_plugin_description(dataset_type)
    possible_keys = ["label", "description", "readOnly"]
    possible_keys.extend(desc["properties"])
    possible_keys.extend(desc["required"])

    # transform the parameter list of tuple to a dictionary
    parameter_dict = {}
    for key, value in parameter:
        if key not in possible_keys:
            raise UsageError(
                f"Configuration key '{key}' is not valid for" f" the dataset type '{dataset_type}'."
            )
        parameter_dict[key] = value

    app.echo_info(f"Updating dataset {dataset_id} ... ", nl=False)
    update_dataset(
        dataset_id=dataset_part,
        project_id=project_part,
        parameters=parameter_dict,
        metadata=_get_metadata_out_of_parameter(parameter_dict),
        read_only=_get_read_only_out_of_parameter(parameter_dict),
        uri_property=parameter_dict.get("uriProperty", ""),
    )
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="open")
@click.argument(
    "dataset_ids", nargs=-1, required=True, type=click.STRING, shell_complete=completion.dataset_ids
)
@click.pass_obj
def open_command(app: ApplicationContext, dataset_ids: tuple[str]) -> None:
    """Open datasets in the browser.

    With this command, you can open a dataset in the workspace in
    your browser.

    The command accepts multiple dataset IDs which results in
    opening multiple browser tabs.
    """
    dataset_urls = {}
    for _ in list_items(item_type="dataset")["results"]:
        dataset_id = _["projectId"] + ":" + _["id"]
        url = _["itemLinks"][0]["path"]
        dataset_urls[dataset_id] = url
    for _ in dataset_ids:
        if _ in dataset_urls:
            full_url = get_cmem_base_uri() + dataset_urls[_]
            app.echo_debug(f"Open {_}: {full_url}")
            click.launch(full_url)
        else:
            raise CmemcError(f"Dataset '{_}' not found.")


@click.group(cls=CmemcGroup)
def dataset() -> CmemcGroup:  # type: ignore[empty-body]
    """List, create, delete, inspect, up-/download or open datasets.

    This command group allows for managing workspace datasets as well as
    dataset file resources. Datasets can be created and deleted.
    File resources can be uploaded and downloaded.
    Details of dataset parameters can be listed with inspect.

    Datasets are identified by a combined key of the PROJECT_ID and
    a DATASET_ID (e.g: `my-project:my-dataset`).

    Note: To get a list of existing datasets, execute the `dataset list`
    command or use tab-completion.
    """


dataset.add_command(list_command)
dataset.add_command(delete_command)
dataset.add_command(download_command)
dataset.add_command(upload_command)
dataset.add_command(inspect_command)
dataset.add_command(create_command)
dataset.add_command(open_command)
dataset.add_command(update_command)
dataset.add_command(resource)
