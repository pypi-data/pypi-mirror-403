"""Build (DataIntegration) variable commands for cmemc."""

from collections import defaultdict

import click
from click import Context, UsageError
from click.shell_completion import CompletionItem
from cmem.cmempy.workspace.projects.variables import (
    create_or_update_variable,
    delete_variable,
    get_all_variables,
    get_variable,
)
from jinja2 import Environment, TemplateSyntaxError, nodes

from cmem_cmemc import completion
from cmem_cmemc.command import CmemcCommand
from cmem_cmemc.command_group import CmemcGroup
from cmem_cmemc.context import ApplicationContext, build_caption
from cmem_cmemc.exceptions import CmemcError
from cmem_cmemc.object_list import (
    DirectMultiValuePropertyFilter,
    DirectValuePropertyFilter,
    MultiFieldPropertyFilter,
    ObjectList,
    compare_regex,
)
from cmem_cmemc.utils import check_or_select_project, split_task_id


def get_variables(ctx: Context) -> list[dict]:  # noqa: ARG001
    """Get variables for object list."""
    _: list[dict] = get_all_variables()
    return _


variable_list_obj = ObjectList(
    name="project variables",
    get_objects=get_variables,
    filters=[
        DirectValuePropertyFilter(
            name="project",
            description="Filter variables by project ID.",
            property_key="project",
            completion_method="values",
        ),
        MultiFieldPropertyFilter(
            name="regex",
            description="Filter by regex matching variable id, value, description, or template.",
            property_keys=["id", "value", "description", "template"],
            compare=compare_regex,
            fixed_completion=[
                CompletionItem("^ending$", help="Variables name ends with 'ending'."),
                CompletionItem("^starting", help="Variables name starts with 'starting'."),
            ],
            fixed_completion_only=False,
        ),
        DirectMultiValuePropertyFilter(
            name="ids",
            description="Internal filter for multiple variable IDs.",
            property_key="id",
        ),
    ],
)


def _extract_dependencies(variable: dict) -> list[str]:
    """Extract variable dependencies from template field using Jinja parser.

    Parses template strings like '{{project.var1}}+{{project.var2}}' to extract
    dependencies. Returns a list of variable IDs that this variable depends on.

    Args:
        variable: Variable dict containing 'template', 'project', and 'id' fields

    Returns:
        List of variable IDs (e.g., ['project:var1', 'project:var2']) that
        this variable depends on

    """
    dependencies: list[str] = []
    template = variable.get("template", "")

    if not template:
        return dependencies

    try:
        # Parse the template using Jinja2's AST
        env = Environment(autoescape=True)
        ast = env.parse(template)

        # Walk through the AST to find all Getattr nodes (attribute access like project.var1)
        for node in ast.find_all(nodes.Getattr):
            # Look for patterns like project.var1 or global.var2
            if isinstance(node.node, nodes.Name) and isinstance(node.attr, str):
                scope = node.node.name  # "project" or "global"
                var_name = node.attr  # "var1", "var2", etc.

                if scope == "project":
                    # Build the full variable ID: projectname:varname
                    project_name = variable["project"]
                    dep_id = f"{project_name}:{var_name}"
                    dependencies.append(dep_id)
                # Note: We skip global variables as they're not in the same deletion scope

    except TemplateSyntaxError:
        # If template parsing fails, return empty dependencies
        # This is safer than failing the entire deletion operation
        pass

    return dependencies


def _sort_variables_by_dependency(variables: list[dict]) -> list[str]:
    """Sort variables in reverse topological order for deletion.

    Variables that depend on others should be deleted first (dependents before
    dependencies). This ensures we don't try to delete a variable that is still
    referenced by another variable's template.

    Args:
        variables: List of variable dicts

    Returns:
        List of variable IDs sorted for safe deletion (dependents first)

    """
    # Build dependency graph: variable_id -> list of variables it depends on
    dependencies: dict[str, list[str]] = {}
    # Build reverse graph: variable_id -> list of variables that depend on it
    dependents: dict[str, list[str]] = defaultdict(list)
    # Track all variable IDs in our deletion set
    variable_ids = {v["id"] for v in variables}

    for variable in variables:
        var_id = variable["id"]
        deps = _extract_dependencies(variable)
        # Only track dependencies within our deletion set
        deps_in_set = [d for d in deps if d in variable_ids]
        dependencies[var_id] = deps_in_set

        for dep_id in deps_in_set:
            dependents[dep_id].append(var_id)

    # Topological sort using Kahn's algorithm (modified for reverse order)
    # We want to delete dependents first, so we start with variables that
    # have no dependents (leaf nodes in the dependency tree)

    # Count how many other variables depend on each variable
    dependent_count = {var_id: len(dependents[var_id]) for var_id in variable_ids}

    # Start with variables that nothing depends on (can be deleted first)
    queue = [var_id for var_id in variable_ids if dependent_count[var_id] == 0]
    # Sort queue to ensure deterministic output
    queue.sort()

    result = []

    while queue:
        # Take the next variable with no dependents
        var_id = queue.pop(0)
        result.append(var_id)

        # For each variable this one depends on, decrease the dependent count
        for dep_id in dependencies[var_id]:
            dependent_count[dep_id] -= 1
            # If no more dependents, can be deleted next
            if dependent_count[dep_id] == 0:
                queue.append(dep_id)
                queue.sort()

    return result


def _validate_variable_ids(variable_ids: tuple[str, ...]) -> None:
    """Validate that provided variable IDs exist."""
    all_variables = get_all_variables()
    all_variable_ids = [_["id"] for _ in all_variables]
    for variable_id in variable_ids:
        if variable_id not in all_variable_ids:
            raise CmemcError(f"Variable {variable_id} not available.")


def _get_variables_to_delete(
    ctx: Context,
    variable_ids: tuple[str, ...],
    all_: bool,
    filter_: tuple[tuple[str, str], ...],
) -> list[dict]:
    """Get the list of variables to delete based on selection method."""
    if all_:
        _: list[dict] = get_all_variables()
        return _

    _validate_variable_ids(variable_ids)

    filter_to_apply = list(filter_) if filter_ else []

    if variable_ids:
        filter_to_apply.append(("ids", ",".join(variable_ids)))

    variables = variable_list_obj.apply_filters(ctx=ctx, filter_=filter_to_apply)

    if not variables and not variable_ids:
        raise CmemcError("No variables found matching the provided filters.")

    return variables


@click.command(cls=CmemcCommand, name="list")
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only variables names and no other metadata. "
    "This is useful for piping the IDs into other commands.",
)
@click.option(
    "--filter",
    "filter_",
    multiple=True,
    type=(str, str),
    shell_complete=variable_list_obj.complete_values,
    help=variable_list_obj.get_filter_help_text(),
)
@click.pass_context
def list_command(ctx: Context, raw: bool, id_only: bool, filter_: tuple[tuple[str, str]]) -> None:
    """List available project variables.

    Outputs a table or a list of project variables.
    """
    app: ApplicationContext = ctx.obj
    variables = variable_list_obj.apply_filters(ctx=ctx, filter_=filter_)

    if raw:
        app.echo_info_json(variables)
        return
    if id_only:
        for _ in sorted(_["id"] for _ in variables):
            app.echo_result(_)
        return
    # output a user table
    table = []
    headers = ["ID", "Value", "Template", "Description"]
    for _ in variables:
        row = [
            _["id"],
            _["value"],
            _.get("template", ""),
            _.get("description", ""),
        ]
        table.append(row)
    filtered = len(filter_) > 0
    app.echo_info_table(
        table,
        headers=headers,
        sort_column=0,
        caption=build_caption(len(table), "project variable", filtered=filtered),
        empty_table_message="No project variables found for these filters."
        if filtered
        else "No project variables found. "
        "Use the `project variable create` command to create a new project variable.",
    )


@click.command(cls=CmemcCommand, name="get")
@click.argument(
    "variable_id", required=True, type=click.STRING, shell_complete=completion.variable_ids
)
@click.option(
    "--key",
    type=click.Choice(["value", "template", "description"], case_sensitive=False),
    default="value",
    show_default=True,
    help="Specify the name of the value you want to get.",
)
@click.option("--raw", is_flag=True, help="Outputs raw json.")
@click.pass_obj
def get_command(app: ApplicationContext, variable_id: str, key: str, raw: bool) -> None:
    """Get the value or other data of a project variable.

    Use the `--key` option to specify which information you want to get.

    Note: Only the `value` key is always available on a project variable.
    Static value variables have no `template` key, and the `description` key
    is optional for both types of variables.
    """
    project_name, variable_name = split_task_id(variable_id)
    _ = get_variable(variable_name=variable_name, project_name=project_name)
    if raw:
        app.echo_info_json(_)
        return
    try:
        app.echo_info(_[key], nl=False)
    except KeyError as error:
        raise UsageError(f"Variable {variable_name} has no value of '{key}'.") from error


@click.command(cls=CmemcCommand, name="delete")
@click.argument("variable_ids", nargs=-1, type=click.STRING, shell_complete=completion.variable_ids)
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Delete all variables. This is a dangerous option, so use it with care.",
)
@click.option(
    "--filter",
    "filter_",
    multiple=True,
    type=(str, str),
    shell_complete=variable_list_obj.complete_values,
    help=variable_list_obj.get_filter_help_text(),
)
@click.pass_context
def delete_command(
    ctx: Context,
    variable_ids: tuple[str, ...],
    all_: bool,
    filter_: tuple[tuple[str, str], ...],
) -> None:
    """Delete project variables.

    There are three selection mechanisms: with specific IDs - only those
    specified variables will be deleted; by using --filter - variables based
    on the filter type and value will be deleted; by using --all, which will
    delete all variables.

    Variables are automatically sorted by their dependencies and deleted in the
    correct order (template-based variables that depend on others are deleted
    first, then their dependencies).
    """
    app: ApplicationContext = ctx.obj

    # Validation: require at least one selection method
    if not variable_ids and not all_ and not filter_:
        raise UsageError(
            "Either specify at least one variable ID or use the --all or "
            "--filter options to specify variables for deletion."
        )

    # Get variables to delete based on selection method
    variables_to_delete = _get_variables_to_delete(ctx, variable_ids, all_, filter_)

    # Remove duplicates while preserving variable objects for dependency analysis
    unique_variables = list({v["id"]: v for v in variables_to_delete}.values())

    # Sort by dependency order (dependents first, then dependencies)
    processed_ids = _sort_variables_by_dependency(unique_variables)
    count = len(processed_ids)

    # Delete each variable
    for current, variable_id in enumerate(processed_ids, start=1):
        project_name, variable_name = split_task_id(variable_id)
        if count > 1:
            current_string = str(current).zfill(len(str(count)))
            app.echo_info(
                f"Delete variable {current_string}/{count}: {variable_name} "
                f"from project {project_name} ... ",
                nl=False,
            )
        else:
            app.echo_info(
                f"Delete variable {variable_name} from project {project_name} ... ", nl=False
            )
        delete_variable(variable_name=variable_name, project_name=project_name)
        app.echo_success("done")


@click.command(cls=CmemcCommand, name="create")
@click.argument(
    "variable_name",
    required=True,
    type=click.STRING,
)
@click.option("--value", type=click.STRING, help="The value of the new project variable.")
@click.option(
    "--template",
    type=click.STRING,
    help="The template of the new project variable. You can use Jinja template "
    "syntax, e.g. use '{{global.myVar}}' for accessing global variables, or "
    "'{{project.myVar}}' for accessing variables from the same project.",
)
@click.option(
    "--description", type=click.STRING, help="The optional description of the new project variable."
)
@click.option(
    "--project",
    "project_id",
    type=click.STRING,
    shell_complete=completion.project_ids,
    help="The project, where you want to create the variable in. If there is "
    "only one project in the workspace, this option can be omitted.",
)
@click.pass_obj
def create_command(  # noqa: PLR0913
    app: ApplicationContext,
    variable_name: str,
    value: str,
    template: str,
    description: str,
    project_id: str,
) -> None:
    """Create a new project variable.

    Variables need to be created with a value or a template (not both).
    In addition to that, a project ID and a name are mandatory.

    Example: cmemc project variable create my_var --project my_project --value abc

    Note: cmemc is currently not able to manage the order of the variables in a
    project. This means you have to create plain value variables in advance,
    before you can create template based variables, which access these values.
    """
    if value and template:
        raise UsageError("Either use '--value' or '--template' but not both.")
    if not value and not template:
        raise UsageError("Use '--value' or '--template' to create a new variable.")
    project_id = check_or_select_project(app, project_id)
    data = get_variable(project_name=project_id, variable_name=variable_name)
    if data:
        raise UsageError(f"Variable '{variable_name}' already exist in project '{project_id}'.")
    data = {"name": variable_name, "isSensitive": False, "scope": "project"}
    if value:
        data["value"] = value
    if template:
        data["template"] = template
    if description:
        data["description"] = description
    app.echo_info(f"Create variable {variable_name} in project {project_id} ... ", nl=False)
    create_or_update_variable(project_name=project_id, variable_name=variable_name, data=data)
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="update")
@click.argument(
    "variable_id", required=True, type=click.STRING, shell_complete=completion.variable_ids
)
@click.option("--value", type=click.STRING, help="The new value of the project variable.")
@click.option(
    "--template",
    type=click.STRING,
    help="The new template of the project variable. You can use Jinja template "
    "syntax, e.g. use '{{global.myVar}}' for accessing global variables, or "
    "'{{project.myVar}}' for accessing variables from the same project.",
)
@click.option(
    "--description", type=click.STRING, help="The new description of the project variable."
)
@click.pass_obj
def update_command(
    app: ApplicationContext,
    variable_id: str,
    value: str,
    template: str,
    description: str,
) -> None:
    """Update data of an existing project variable.

    With this command you can update the value or the template, as well as the
    description of a project variable.

    Note: If you update the template of a static variable, it will be transformed
    to a template based variable. If you want to change the value of a template
    based variable, an error will be shown.
    """
    project_id, variable_name = split_task_id(variable_id)
    data = get_variable(project_name=project_id, variable_name=variable_name)
    if not data:
        raise UsageError(f"Variable '{variable_name}' does not exist in project '{project_id}'.")
    if value and template:
        raise UsageError(
            "Project variables are based on a static value or on a template, but not " "both."
        )
    if not value and not template and not description:
        raise UsageError(
            "Please specify what you want to update. "
            "Use at least one of the following options: "
            "'--value', '--template', '--description'."
        )
    if value:
        if data.get("template", None):
            raise UsageError("You can not change the value of a template based variable.")
        data["value"] = value
    if template:
        if not data.get("template", None):
            app.echo_warning(
                f"Variable '{variable_id}' will be converted from a "
                f"simple to a template based variable."
            )
        data["template"] = template
    if description:
        data["description"] = description
    app.echo_info(f"Update variable {variable_name} in project {project_id} ... ", nl=False)
    create_or_update_variable(project_name=project_id, variable_name=variable_name, data=data)
    app.echo_success("done")


@click.group(cls=CmemcGroup)
def variable() -> CmemcGroup:  # type: ignore[empty-body]
    """List, create, delete or get data from project variables.

    Project variables can be used in dataset and task parameters, and in the template
    transform operator.
    Variables are either based on a static value or based on a template.
    They may use templates that access globally configured
    variables or other preceding variables from the same project.

    Variables are identified by a VARIABLE_ID. To get a list of existing
    variables, execute the list command or use tab-completion.
    The VARIABLE_ID is a concatenation of a PROJECT_ID and a VARIABLE_NAME,
    such as `my-project:my-variable`.
    """


variable.add_command(list_command)
variable.add_command(get_command)
variable.add_command(delete_command)
variable.add_command(create_command)
variable.add_command(update_command)
