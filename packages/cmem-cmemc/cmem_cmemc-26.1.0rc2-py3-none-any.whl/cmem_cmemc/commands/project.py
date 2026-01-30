"""Enhanced project.py with filtering capabilities."""

import os
import pathlib
import shutil
import tempfile
from zipfile import ZipFile

import click
from click import Context, UsageError
from cmem.cmempy.config import get_di_api_endpoint
from cmem.cmempy.plugins.marshalling import (
    get_extension_by_plugin,
    get_marshalling_plugins,
)
from cmem.cmempy.workspace.projects.export_ import export_project
from cmem.cmempy.workspace.projects.import_ import (
    import_from_upload_start,
    import_from_upload_status,
    upload_project,
)
from cmem.cmempy.workspace.projects.project import (
    create_project_with_transformation,
    delete_project,
    get_failed_tasks_report,
    get_projects,
    make_new_project_with_metadata,
    reload_project,
)
from jinja2 import Template

from cmem_cmemc import completion
from cmem_cmemc.command import CmemcCommand
from cmem_cmemc.command_group import CmemcGroup
from cmem_cmemc.commands.file import file
from cmem_cmemc.commands.variable import variable
from cmem_cmemc.context import ApplicationContext, build_caption
from cmem_cmemc.exceptions import CmemcError
from cmem_cmemc.object_list import (
    DirectListPropertyFilter,
    DirectValuePropertyFilter,
    Filter,
    MultiFieldPropertyFilter,
    ObjectList,
)
from cmem_cmemc.parameter_types.path import ClickSmartPath
from cmem_cmemc.smart_path import SmartPath as Path
from cmem_cmemc.string_processor import ProjectLink, TimeAgo


def get_projects_for_list(ctx: Context) -> list[dict]:
    """Get projects for object list, transforming structure for filtering."""
    _ = ctx
    # Transform the project structure to flatten metadata for easier filtering
    transformed = []
    for _ in get_projects():
        transformed_project = {
            "name": _["name"],
            "label": _["metaData"].get("label", ""),
            "description": _["metaData"].get("description", ""),
            "tags": _["metaData"].get("tags", []),
            "modified": _["metaData"].get("modified", ""),
            "lastModifiedByUser": _["metaData"].get("lastModifiedByUser", ""),
            # Keep original for reference
            "_original": _,
        }
        transformed.append(transformed_project)
    return transformed


def transform_tag_uris_to_labels(ctx: Filter, value: list) -> list:
    """Transform tag URIs to their label equivalents for filtering.

    Extracts the label portion from URIs like 'urn:silkframework:tag:mytag'
    """
    import urllib.parse

    _ = ctx
    labels = []
    for tag_uri in value:
        if isinstance(tag_uri, str) and ":" in tag_uri:
            label = tag_uri.split(":")[-1]
            label = urllib.parse.unquote(label)
            labels.append(label)
    return labels


# Create the project list object with filters
project_list = ObjectList(
    name="projects",
    get_objects=get_projects_for_list,
    filters=[
        DirectValuePropertyFilter(
            name="id",
            description="Filter by project ID (name).",
            property_key="name",
            completion_method="values",
        ),
        MultiFieldPropertyFilter(
            name="regex",
            description="Filter by regex matching project name, label, or description.",
            property_keys=["name", "label", "description"],
        ),
        DirectListPropertyFilter(
            name="tag",
            description="Filter by tag label.",
            property_key="tags",
            transform=transform_tag_uris_to_labels,
        ),
    ],
)


def _validate_projects_to_process(project_ids: tuple[str], all_flag: bool) -> list[str]:
    """Return a list project IDs which will be processed.

    list of IDs is without duplicates, and validated if they exist
    """
    if project_ids == () and not all_flag:
        raise UsageError(
            "Either specify at least one project ID "
            "or use the --all option to process over all projects."
        )
    projects_to_process = list(project_ids)
    all_projects = [_["name"] for _ in get_projects()]
    if all_flag:
        # in case --all is given, a list of project is fetched
        projects_to_process = all_projects
    # avoid double removal
    projects_to_process = list(set(projects_to_process))

    # test if one of the projects does NOT exist
    for _ in projects_to_process:
        if _ not in all_projects:
            raise CmemcError(f"Project {_} does not exist.")
    return projects_to_process


def _show_type_list(app: ApplicationContext) -> None:
    """Output the list of project export types.

    Internally this is named marshalling plugin.

    Args:
    ----
        app (ApplicationContext): the click cli app context.

    """
    types = get_marshalling_plugins()
    table = []
    for _ in types:
        id_ = _["id"]
        label = _["label"]
        description = _["description"].partition("\n")[0]
        row = [
            id_,
            f"{label}: {description}",
        ]
        table.append(row)
    app.echo_info_table(table, headers=["Export Type", "Description"], sort_column=1)


@click.command(cls=CmemcCommand, name="open")
@click.argument(
    "project_ids", nargs=-1, required=True, type=click.STRING, shell_complete=completion.project_ids
)
@click.pass_obj
def open_command(app: ApplicationContext, project_ids: tuple[str]) -> None:
    """Open projects in the browser.

    With this command, you can open a project in the workspace in
    your browser to change them.

    The command accepts multiple project IDs which results in
    opening multiple browser tabs.
    """
    projects = get_projects()
    for _ in project_ids:
        if _ not in (p["name"] for p in projects):
            raise CmemcError(f"Project '{_}' not found.")
        open_project_uri = f"{get_di_api_endpoint()}/workbench/projects/{_}"
        app.echo_debug(f"Open {_}: {open_project_uri}")
        click.launch(open_project_uri)


@click.command(cls=CmemcCommand, name="list")
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    multiple=True,
    shell_complete=project_list.complete_values,
    help=project_list.get_filter_help_text(),
)
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only project identifier and no labels or other "
    "metadata. This is useful for piping the IDs into other commands.",
)
@click.pass_context
def list_command(ctx: Context, filter_: tuple[tuple[str, str]], raw: bool, id_only: bool) -> None:
    """List available projects.

    Outputs a list of project IDs which can be used as reference for
    the project create, delete, export and import commands.
    """
    app = ctx.obj

    # Apply filters
    filtered_projects = project_list.apply_filters(ctx=ctx, filter_=filter_)

    # Extract original project data for output
    projects = [p["_original"] for p in filtered_projects]

    if raw:
        app.echo_info_json(projects)
        return
    if id_only:
        for _ in sorted(projects, key=lambda k: k["name"].lower()):
            app.echo_result(_["name"])
        return

    # output a user table
    # Create a dict mapping project names to project data for the ProjectLink processor
    projects_dict = {_["name"]: _ for _ in projects}
    table = []
    for _ in projects:
        # Extract modified timestamp from nested metaData
        metadata = _.get("metaData", {})
        modified = metadata.get("modified", "")

        row = [
            _["name"],
            modified,
            _["name"],  # Pass project ID to be processed by ProjectLink
        ]
        table.append(row)

    filtered = len(filter_) > 0
    app.echo_info_table(
        table,
        headers=["Project ID", "Modified", "Label"],
        sort_column=1,
        caption=build_caption(len(table), "project", filtered=filtered),
        empty_table_message="No projects found for these filters."
        if filtered
        else "No projects found. Use the `project create` command to create a new project.",
        cell_processing={1: TimeAgo(), 2: ProjectLink(projects=projects_dict)},
    )


@click.command(cls=CmemcCommand, name="delete")
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Delete all projects. " "This is a dangerous option, so use it with care.",
)
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    multiple=True,
    shell_complete=project_list.complete_values,
    help=project_list.get_filter_help_text(),
)
@click.argument("project_ids", nargs=-1, type=click.STRING, shell_complete=completion.project_ids)
@click.pass_context
def delete_command(
    ctx: Context,
    all_: bool,
    filter_: tuple[tuple[str, str]],
    project_ids: tuple[str],
) -> None:
    """Delete projects.

    This command deletes existing data integration projects from Corporate
    Memory.

    Warning: Projects will be deleted without prompting!

    Note: Projects can be listed with the `project list` command.
    """
    app = ctx.obj

    if project_ids == () and not all_ and not filter_:
        raise UsageError(
            "Either specify at least one project ID"
            " or use a --filter option,"
            " or use the --all option to delete all projects."
        )

    if project_ids and (all_ or filter_):
        raise UsageError("Either specify a project ID OR use a --filter or the --all option.")

    if all_ or filter_:
        # in case --all or --filter is given, a list of projects is fetched
        project_ids = []
        filtered_projects = project_list.apply_filters(ctx=ctx, filter_=filter_)
        for _ in filtered_projects:
            project_ids.append(_["name"])

    # Avoid double removal as well as sort project IDs
    projects_to_delete = sorted(set(project_ids), key=lambda v: v.lower())
    count = len(projects_to_delete)
    for current, project_id in enumerate(projects_to_delete, start=1):
        current_string = str(current).zfill(len(str(count)))
        app.echo_info(f"Delete project {current_string}/{count}: {project_id} ... ", nl=False)
        delete_project(project_id)
        app.echo_success("deleted")


@click.command(cls=CmemcCommand, name="create")
@click.argument("project_ids", nargs=-1, required=True, type=click.STRING)
@click.option(
    "--from-transformation",
    nargs=1,
    shell_complete=completion.transformation_task_ids,
    required=False,
    help=(
        "This option can be used to explicitly create the link specification, "
        "which is internally executed when using the mapping suggestion of "
        "a transformation task. You need the task ID of the transformation task."
    ),
)
@click.option(
    "--label",
    "labels",
    multiple=True,
    help="Give the label of the project. You can give more than one label if you"
    " create more than one project.",
)
@click.option(
    "--description",
    "descriptions",
    multiple=True,
    help="Give the description of the project. You can give more than one description"
    " if you create more than one project.",
)
@click.pass_obj
def create_command(
    app: ApplicationContext,
    project_ids: tuple[str],
    from_transformation: str,
    labels: tuple[str],
    descriptions: tuple[str],
) -> None:
    """Create projects.

    This command creates one or more new projects.
    Existing projects will not be overwritten.

    Note: Projects can be listed by using the `project list` command.
    """
    if from_transformation and len(project_ids) > 1:
        raise UsageError(
            "By using --from-transformation,"
            " the project ID parameter is limited to a single project ID."
        )

    all_projects = [_["name"] for _ in get_projects()]
    for project_id in project_ids:
        if project_id in all_projects:
            raise CmemcError(f"Project {project_id} already exists.")

    if from_transformation:
        transformation_parts = from_transformation.split(":")
        transformation_project, transformation_task_id = (
            transformation_parts[0],
            transformation_parts[1],
        )
        app.echo_info(
            f"Create new project {project_ids[0]} from transformation"
            f" {transformation_task_id} ... ",
            nl=False,
        )
        create_project_with_transformation(
            transform_project_id=transformation_project,
            transform_task_id=transformation_task_id,
            matching_link_spec_project_id=project_ids[0],
            matching_link_spec_id=f"linking_{transformation_task_id.split('_')[-1]}",
        )
        app.echo_success("done")
        return

    count = len(project_ids)
    current = 1
    if len(labels) > 0 and len(labels) != count:
        raise UsageError(
            "Either give labels for all projects or for no project."
            f" Got {len(labels)} labels but {count} projects."
        )
    if len(descriptions) > 0 and len(descriptions) != count:
        raise UsageError(
            "Either give descriptions for all projects or for no project."
            f" Got {len(descriptions)} descriptions but {count} projects."
        )

    for project_id in project_ids:
        try:
            label = labels[current - 1]
        except IndexError:
            label = project_id
        try:
            description = descriptions[current - 1]
        except IndexError:
            description = ""
        app.echo_info(f"Create new project {current}/{count}: {project_id} ... ", nl=False)
        app.echo_debug(get_projects())
        make_new_project_with_metadata(project_id, label=label, description=description)
        app.echo_success("done")
        current = current + 1


@click.command(cls=CmemcCommand, name="export")
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Export all projects.",
)
@click.option(
    "-o",
    "--overwrite",
    is_flag=True,
    hidden=True,
)
@click.option(
    "--replace",
    is_flag=True,
    help="Replace existing files. This is a dangerous option, so use it with care.",
)
@click.option(
    "--output-dir",
    default=".",
    show_default=True,
    type=ClickSmartPath(writable=True, file_okay=False),
    help="The base directory, where the project files will be created. "
    "If this directory does not exist, it will be silently created.",
)
@click.option(
    "--type",
    "marshalling_plugin",
    default="xmlZip",
    show_default=True,
    type=click.STRING,
    shell_complete=completion.marshalling_plugins,
    help="Type of the exported project file(s). Use the --help-types option "
    "or tab completion to see a list of possible types.",
)
@click.option(
    "--filename-template",
    "-t",
    "template",
    default="{{date}}-{{connection}}-{{id}}.project",
    show_default=True,
    type=click.STRING,
    shell_complete=completion.project_export_templates,
    help="Template for the export file name(s). Possible placeholders are (Jinja2): "
    "{{id}} (the project ID), "
    "{{connection}} (from the --connection option) and "
    "{{date}} (the current date as YYYY-MM-DD). "
    "The file suffix will be appended. Needed directories will be created.",
)
@click.option(
    "--extract",
    is_flag=True,
    help="Export projects to a directory structure instead of a ZIP archive. "
    "Note that the --filename-template "
    "option is ignored here. Instead, a sub-directory per exported "
    "project is created under the output directory. "
    "Also note that not all export types are extractable.",
)
@click.option("--help-types", is_flag=True, help="Lists all possible export types.")
@click.argument("project_ids", nargs=-1, type=click.STRING, shell_complete=completion.project_ids)
@click.pass_obj
def export_command(  # noqa: PLR0913
    app: ApplicationContext,
    all_: bool,
    project_ids: tuple[str],
    overwrite: bool,
    replace: bool,
    marshalling_plugin: str,
    template: str,
    output_dir: str,
    extract: bool,
    help_types: bool,
) -> None:
    """Export projects to files.

    Projects can be exported with different export formats.
    The default type is a zip archive which includes metadata as well
    as dataset resources.
    If more than one project is exported, a file is created for each project.
    By default, these files are created in the current directory with a
    descriptive name (see --template option default).

    Note: Projects can be listed by using the `project list` command.

    You can use the template string to create subdirectories.

    Example: cmemc config list | parallel -I% cmemc -c % project export --all
    -t "dump/{{connection}}/{{date}}-{{id}}.project"
    """
    if overwrite:
        replace = overwrite
        app.echo_warning(
            "The option --overwrite is deprecated and will be removed with the next major release."
            " Please use the --replace option instead."
        )

    if help_types:
        _show_type_list(app)
        return

    extractable_types = ("xmlZip", "xmlZipWithoutResources")
    if extract and marshalling_plugin not in extractable_types:
        raise UsageError(
            f"The export type {marshalling_plugin} can not be extracted. "
            f"Use one of {extractable_types}."
        )

    projects_to_export = _validate_projects_to_process(project_ids=project_ids, all_flag=all_)
    count = len(projects_to_export)
    template_data = app.get_template_data()
    for current, project_id in enumerate(projects_to_export, start=1):
        # prepare the template data and prepare target path name
        template_data.update(id=project_id)
        if extract:
            # this name is only used of display
            # the ZIP has first level directory
            local_name = project_id
        else:
            local_name = (
                Template(template).render(template_data)
                + "."
                + get_extension_by_plugin(marshalling_plugin)
            )
        # join with given output directory and normalize full path
        export_path = os.path.normpath(str(Path(output_dir) / local_name))

        app.echo_info(
            f"Export project {current}/{count}: " f"{project_id} to {export_path} ... ", nl=False
        )
        if Path(export_path).exists() and replace is not True:
            app.echo_error("target file or directory exists")
            continue

        Path(export_path).parent.mkdir(exist_ok=True, parents=True)

        if extract:
            export_data = export_project(project_id, marshalling_plugin)
            # do the export to a temp file and extract it afterward
            with tempfile.NamedTemporaryFile() as tmp_file:
                app.echo_debug(f"Temporary file is {tmp_file.name}")
                tmp_file.write(export_data)
                shutil.rmtree(export_path, ignore_errors=True)
                with ZipFile(tmp_file, "r") as _:
                    _.extractall(output_dir)
        else:
            export_data = export_project(project_id, marshalling_plugin)
            # create parent directory
            Path(export_path).parent.absolute().mkdir(exist_ok=True)
            with Path(export_path).open(mode="wb") as _:
                _.write(export_data)

        app.echo_success("done")


@click.command(cls=CmemcCommand, name="import")
@click.argument(
    "path",
    shell_complete=completion.project_files,
    type=ClickSmartPath(
        allow_dash=False, dir_okay=True, readable=True, exists=True, remote_okay=True
    ),
)
@click.argument(
    "project_id",
    type=click.STRING,
    required=False,
    default="",
    shell_complete=completion.project_ids,
)
@click.option(
    "-o",
    "--overwrite",
    is_flag=True,
    hidden=True,
)
@click.option(
    "--replace",
    is_flag=True,
    help="Replace an existing project. This is a dangerous option, so use it with care.",
)
@click.pass_obj
def import_command(
    app: ApplicationContext, path: str, project_id: str, overwrite: bool, replace: bool
) -> None:
    """Import a project from a file or directory.

    Example: cmemc project import my_project.zip my_project
    """
    if overwrite:
        replace = overwrite
        app.echo_warning(
            "The option --overwrite is deprecated and will be removed with the next major release."
            " Please use the --replace option instead."
        )

    all_projects = get_projects()
    if project_id and not replace and project_id in ([_["name"] for _ in all_projects]):
        raise CmemcError(f"Project {project_id} is already there.")

    if Path(path).is_dir():
        if not (Path(path) / "config.xml").is_file():
            # fail early if directory is not an export
            raise CmemcError(f"Directory {path} seems not to be a export directory.")

        app.echo_info(f"Import directory {path} to project {project_id} ... ", nl=False)
        # in case of a directory, we zip it to a temp file
        app.echo_info("zipping ... ", nl=False)
        with tempfile.NamedTemporaryFile() as _:
            shutil.make_archive(
                _.name,
                "zip",
                base_dir=pathlib.Path(path).name,
                root_dir=str(Path(path).parent.absolute()),
            )
            # make_archive adds a .zip automatically ...
            uploaded_file = _.name + ".zip"
            app.echo_debug(f"Uploaded file is {uploaded_file}")
    else:
        app.echo_info(f"Import file {path} to project {project_id} ... ", nl=False)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as _:
            with ClickSmartPath.open(path) as _buffer:
                _.write(_buffer.read())
            uploaded_file = _.name

    # upload file and get validation report
    validation_response = upload_project(uploaded_file)
    # Remove the temporary file
    pathlib.Path.unlink(pathlib.Path(uploaded_file))
    if "errorMessage" in validation_response:
        raise CmemcError(validation_response["errorMessage"])
    import_id = validation_response["projectImportId"]

    # get project_id from response if not given as parameter
    if not project_id:
        project_id = validation_response["projectId"]

    app.echo_debug(f"File {uploaded_file} uploaded: {validation_response}")

    # start import of project from upload using import ID as a reference
    # this fails if project_id already exists
    import_from_upload_start(import_id=import_id, project_id=project_id, overwrite_existing=replace)

    # loop until "success" boolean is in status response
    status = import_from_upload_status(import_id)
    while "success" not in status:
        status = import_from_upload_status(import_id)
    if status["success"] is True:
        app.echo_success("done")
        # output warnings in case there are failed tasks errors
        for _ in get_failed_tasks_report(project_id):
            app.echo_warning(_["errorMessage"])
    else:
        app.echo_error(" error")
    app.echo_debug(f"last import status: {status}")


@click.command(cls=CmemcCommand, name="reload")
@click.option("-a", "--all", "all_", is_flag=True, help="Reload all projects")
@click.argument("project_ids", nargs=-1, type=click.STRING, shell_complete=completion.project_ids)
@click.pass_obj
def reload_command(app: ApplicationContext, all_: bool, project_ids: tuple[str]) -> None:
    """Reload projects from the workspace provider.

    This command reloads all tasks of a project from the workspace provider.
    This is similar to the `workspace reload` command, but for a
    single project only.

    Note: You need this in case you changed project data externally or loaded
    a project which uses plugins which are not installed yet.
    In this case, install the plugin(s) and reload the project afterward.

    Warning: Depending on the size your datasets esp. your Knowledge Graphs,
    reloading a project can take a long time to re-create the path caches.
    """
    projects_to_reload = _validate_projects_to_process(project_ids=project_ids, all_flag=all_)
    count = len(projects_to_reload)
    for current, project_id in enumerate(projects_to_reload, start=1):
        app.echo_info(f"Reload project {current}/{count}: {project_id} ... ", nl=False)
        reload_project(project_id)
        app.echo_success("done")


@click.group(cls=CmemcGroup)
def project() -> CmemcGroup:  # type: ignore[empty-body]
    """List, import, export, create, delete or open projects.

    Projects are identified by a PROJECT_ID.

    Note: To get a list of existing projects, execute the `project list`
    command or use tab-completion.
    """


project.add_command(open_command)
project.add_command(list_command)
project.add_command(export_command)
project.add_command(import_command)
project.add_command(delete_command)
project.add_command(create_command)
project.add_command(reload_command)
project.add_command(variable)
project.add_command(file)
