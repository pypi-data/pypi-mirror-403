"""access control"""

import json
import os

import click
import requests.exceptions
from click import Context, Option
from cmem.cmempy.dp.authorization.conditions import (
    create_access_condition,
    delete_access_condition,
    fetch_all_acls,
    get_access_condition_by_iri,
    review_graph_rights,
    update_access_condition,
)
from cmem.cmempy.keycloak.user import get_user_by_username, user_groups
from jinja2 import Template

from cmem_cmemc import completion
from cmem_cmemc.command import CmemcCommand
from cmem_cmemc.command_group import CmemcGroup
from cmem_cmemc.constants import NS_ACL, NS_ACTION, NS_GROUP, NS_USER
from cmem_cmemc.context import ApplicationContext, build_caption
from cmem_cmemc.object_list import (
    DirectListPropertyFilter,
    DirectMultiValuePropertyFilter,
    DirectValuePropertyFilter,
    ObjectList,
)
from cmem_cmemc.parameter_types.path import ClickSmartPath
from cmem_cmemc.smart_path import SmartPath as Path
from cmem_cmemc.utils import (
    convert_iri_to_qname,
    convert_qname_to_iri,
    get_query_text,
    struct_to_table,
)

# option descriptions
HELP_TEXTS = {
    "name": "A optional name.",
    "id": "An optional ID (will be an UUID otherwise).",
    "description": "An optional description.",
    "user": "A specific user account required by the access condition.",
    "group": "A membership in a user group required by the access condition.",
    "read_graph": "Grants read access to a graph.",
    "write_graph": "Grants write access to a graph (includes read access).",
    "action": "Grants usage permissions to an action / functionality.",
    "read_graph_pattern": (
        "Grants management of conditions granting read access on graphs matching the defined "
        "pattern. A pattern consists of a constant string and a wildcard ('*') at the end of "
        "the pattern or the wildcard alone."
    ),
    "write_graph_pattern": (
        "Grants management of conditions granting write access on graphs matching the defined "
        "pattern. A pattern consists of a constant string and a wildcard ('*') at the end of "
        "the pattern or the wildcard alone."
    ),
    "action_pattern": (
        "Grants management of conditions granting action allowance for actions matching the "
        "defined pattern. A pattern consists of a constant string and a wildcard ('*') at the "
        "end of the pattern or the wildcard alone."
    ),
    "query": "Dynamic access condition query (file or the query catalog IRI).",
    "replace": (
        "Replace (overwrite) existing access condition, if present. "
        "Can be used only in combination with '--id'."
    ),
}

WARNING_UNKNOWN_USER = "Unknown User or no access to get user info."
WARNING_NO_GROUP_ACCESS = "You do not have the permission to retrieve user groups"
WARNING_USE_GROUP = "Use the --group option to assign groups manually (what-if-scenario)."

PUBLIC_USER_URI = "https://vocab.eccenca.com/auth/AnonymousUser"
PUBLIC_GROUP_URI = "https://vocab.eccenca.com/auth/PublicGroup"

KNOWN_ACCESS_CONDITION_URLS = [PUBLIC_USER_URI, PUBLIC_GROUP_URI]


def _list_to_acl_url(ctx: ApplicationContext, param: Option, value: list) -> list:
    """Option callback which returns a URI for a list of strings.

    or list of URIs, if a tuple comes from click
    or not, if it is already a known URI .... or None
    """
    return [_value_to_acl_url(ctx, param, _) for _ in value]


def _value_to_acl_url(
    ctx: ApplicationContext,  # noqa: ARG001
    param: Option,
    value: str | None,
) -> str | None:
    """Option callback which returns a URI for a string.

    or not, if it is already a known URI .... or None
    """
    if value == "" or value is None:
        return value
    if value.startswith(("http://", "https://")):
        return value
    match param.name:
        case "groups":
            return f"{NS_GROUP}{value}"
        case "user":
            return f"{NS_USER}{value}"
    return f"{NS_ACL}{value}"


def generate_acl_name(user: str | None, groups: list[str], query: str | None) -> str:
    """Create an access condition name based on user and group assignments."""
    if query is not None:
        return "Query based Dynamic Access Condition"
    if len(groups) > 0:
        group_term = "groups" if len(groups) > 1 else "group"
        groups_labels = ", ".join(
            [convert_iri_to_qname(iri=_, default_ns=NS_GROUP)[1:] for _ in groups]
        )
        if user:
            return (
                f"Condition for user {convert_iri_to_qname(iri=user, default_ns=NS_USER)[1:]} "
                f"and {group_term} {groups_labels}"
            )
        return f"Condition for {group_term} {groups_labels}"
    if user:
        return f"Condition for user: {convert_iri_to_qname(iri=user, default_ns=NS_USER)[1:]}"
    return "Condition for ALL users"


def get_acls(ctx: Context) -> list[dict]:  # noqa: ARG001
    """Get access conditions for object list"""
    return fetch_all_acls()  # type: ignore[no-any-return]


acl_list = ObjectList(
    name="access conditions",
    get_objects=get_acls,
    filters=[
        DirectMultiValuePropertyFilter(
            name="ids",
            description="Access conditions with a specific ID.",
            property_key="iri",
        ),
        DirectValuePropertyFilter(
            name="name",
            description="List only access conditions with a specific name.",
            property_key="name",
        ),
        DirectValuePropertyFilter(
            name="user",
            description="List only access conditions that require a specific user account.",
            property_key="requiresAccount",
        ),
        DirectListPropertyFilter(
            name="group",
            description="List only access conditions that require membership in a specific group.",
            property_key="requiresGroup",
        ),
        DirectListPropertyFilter(
            name="read-graph",
            description="List only access conditions that grant read access to a specific graph.",
            property_key="readableGraphs",
        ),
        DirectListPropertyFilter(
            name="write-graph",
            description="List only access conditions that grant write access to a specific graph.",
            property_key="writableGraphs",
        ),
    ],
)


def _validate_acl_ids(access_condition_ids: tuple[str, ...]) -> None:
    """Validate that all provided access condition IDs exist."""
    if not access_condition_ids:
        return
    all_acls = fetch_all_acls()
    all_iris = {acl["iri"] for acl in all_acls}
    for acl_id in access_condition_ids:
        iri = convert_qname_to_iri(qname=acl_id, default_ns=NS_ACL)
        if iri not in all_iris:
            raise click.ClickException(
                f"Access condition {acl_id} not available. Use the 'admin acl list' "
                "command to get a list of existing access conditions."
            )


def _get_acls_to_delete(
    ctx: Context,
    access_condition_ids: tuple[str, ...],
    all_: bool,
    filter_: tuple[tuple[str, str], ...],
) -> list[dict]:
    """Get the list of access conditions to delete based on selection method."""
    if all_:
        # Get all access conditions
        return fetch_all_acls()  # type: ignore[no-any-return]

    # Validate provided IDs exist before proceeding
    _validate_acl_ids(access_condition_ids)

    # Build filter list
    filter_to_apply = list(filter_) if filter_ else []

    # Add IDs if provided (using internal multi-value filter)
    if access_condition_ids:
        iris = [convert_qname_to_iri(qname=_, default_ns=NS_ACL) for _ in access_condition_ids]
        filter_to_apply.append(("ids", ",".join(iris)))

    # Apply filters
    acls = acl_list.apply_filters(ctx=ctx, filter_=filter_to_apply)

    # Validation: ensure we found access conditions
    if not acls and not access_condition_ids:
        raise click.ClickException("No access conditions found matching the provided filters.")

    return acls


@click.command(cls=CmemcCommand, name="list")
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only URIs. This is useful for piping the IDs into other commands.",
)
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    multiple=True,
    help=acl_list.get_filter_help_text(),
    shell_complete=acl_list.complete_values,
)
@click.pass_context
def list_command(ctx: Context, raw: bool, id_only: bool, filter_: tuple[tuple[str, str]]) -> None:
    """List access conditions.

    This command retrieves and lists all access conditions, which are manageable
    by the current account.
    """
    app: ApplicationContext = ctx.obj
    acls = acl_list.apply_filters(ctx=ctx, filter_=filter_)
    if raw:
        app.echo_info_json(acls)
        return
    if id_only:
        for _ in acls:
            app.echo_info(convert_iri_to_qname(iri=_.get("iri"), default_ns=NS_ACL))
        return
    table = [
        (convert_iri_to_qname(iri=_.get("iri"), default_ns=NS_ACL), _.get("name", "-"))
        for _ in acls
    ]
    app.echo_info_table(
        table,
        headers=["URI", "Name"],
        sort_column=0,
        caption=build_caption(len(table), "access condition"),
        empty_table_message="No access conditions found. "
        "Use the `admin acl create` command to create a new access condition.",
    )


@click.command(cls=CmemcCommand, name="inspect")
@click.argument("access_condition_id", type=click.STRING, shell_complete=completion.acl_ids)
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.pass_obj
def inspect_command(app: ApplicationContext, access_condition_id: str, raw: bool) -> None:
    """Inspect an access condition.

    Note: access conditions can be listed by using the `acl list` command.
    """
    iri = convert_qname_to_iri(qname=access_condition_id, default_ns=NS_ACL)
    access_condition = get_access_condition_by_iri(iri).json()

    if raw:
        app.echo_info_json(access_condition)
        return

    table = struct_to_table(access_condition)
    app.echo_info_table(table, headers=["Key", "Value"], sort_column=0)


@click.command(cls=CmemcCommand, name="create")
@click.option(
    "--user",
    type=click.STRING,
    shell_complete=completion.acl_users,
    help=HELP_TEXTS["user"],
    callback=_value_to_acl_url,
)
@click.option(
    "--group",
    "groups",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.acl_groups,
    help=HELP_TEXTS["group"],
    callback=_list_to_acl_url,
)
@click.option(
    "--read-graph",
    "read_graphs",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.graph_uris_with_all_graph_uri,
    help=HELP_TEXTS["read_graph"],
)
@click.option(
    "--write-graph",
    "write_graphs",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.graph_uris_with_all_graph_uri,
    help=HELP_TEXTS["write_graph"],
)
@click.option(
    "--action",
    "actions",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.acl_actions,
    help=HELP_TEXTS["action"],
)
@click.option(
    "--read-graph-pattern",
    "read_graph_patterns",
    type=click.STRING,
    multiple=True,
    help=HELP_TEXTS["read_graph_pattern"],
)
@click.option(
    "--write-graph-pattern",
    "write_graph_patterns",
    type=click.STRING,
    multiple=True,
    help=HELP_TEXTS["write_graph_pattern"],
)
@click.option(
    "--action-pattern",
    "action_patterns",
    type=click.STRING,
    multiple=True,
    help=HELP_TEXTS["action_pattern"],
)
@click.option(
    "--query",
    "query",
    type=click.STRING,
    shell_complete=completion.remote_queries_and_sparql_files,
    help=HELP_TEXTS["query"],
)
@click.option(
    "--id",
    "id_",
    type=click.STRING,
    help=HELP_TEXTS["id"],
)
@click.option(
    "--name",
    "name",
    type=click.STRING,
    help=HELP_TEXTS["name"],
)
@click.option(
    "--description",
    "description",
    type=click.STRING,
    help=HELP_TEXTS["description"],
)
@click.option("--replace", is_flag=True, help=HELP_TEXTS["replace"])
@click.pass_obj
def create_command(  # noqa: PLR0913
    app: ApplicationContext,
    name: str,
    id_: str,
    description: str,
    user: str,
    groups: list[str],
    read_graphs: tuple[str],
    write_graphs: tuple[str],
    actions: tuple[str],
    read_graph_patterns: tuple[str],
    write_graph_patterns: tuple[str],
    action_patterns: tuple[str],
    query: str,
    replace: bool,
) -> None:
    """Create an access condition.

    With this command, new access conditions can be created.

    An access condition captures information about WHO gets access to WHAT.
    In order to specify WHO gets access, use the `--user` and / or `--group` options.
    In order to specify WHAT an account get access to, use the `--read-graph`,
    `--write-graph` and `--action` options.`

    In addition to that, you can specify a name, a description and an ID (all optional).

    A special case are dynamic access conditions, based on a SPARQL query: Here you
    have to provide a query with the projection variables `user`, `group` `readGraph`
    and `writeGraph` to create multiple grants at once. You can either provide a query file
    or a query URL from the query catalog.

    Note: Queries for dynamic access conditions are copied into the ACL, so changing the
    query in the query catalog does not change it in the access condition.

    Example: cmemc admin acl create --group local-users --write-graph https://example.org/
    """
    if replace and not id_:
        raise click.UsageError("To replace an access condition, you must specify an ID.")

    if (
        not read_graphs
        and not write_graphs
        and not actions
        and not read_graph_patterns
        and not write_graph_patterns
        and not action_patterns
        and not query
    ):
        raise click.UsageError(
            "Missing access / usage grant. Use at least one of the following options: "
            "--read-graph, --write-graph, --action, --read-graph-pattern, "
            "--write-graph-pattern, --action-pattern or --query."
        )
    query_str = None
    if query:
        query_str = get_query_text(query, {"user", "group", "readGraph", "writeGraph"})

    if not user and not groups and not query:
        app.echo_warning("Access conditions without a user or group assignment affects ALL users.")

    if not name:
        name = generate_acl_name(user=user, groups=groups, query=query)

    if not description:
        description = "This access condition was created with cmemc."

    if replace and NS_ACL + id_ in [_["iri"] for _ in fetch_all_acls()]:
        app.echo_info(f"Replacing access condition '{id_}' ... ", nl=False)
        delete_access_condition(iri=NS_ACL + id_)
    else:
        app.echo_info(f"Creating access condition '{name}' ... ", nl=False)
    create_access_condition(
        name=name,
        static_id=id_,
        description=description,
        user=user,
        groups=groups,
        read_graphs=list(read_graphs),
        write_graphs=list(write_graphs),
        actions=[convert_qname_to_iri(qname=_, default_ns=NS_ACTION) for _ in actions],
        read_graph_patterns=list(read_graph_patterns),
        write_graph_patterns=list(write_graph_patterns),
        action_patterns=list(action_patterns),
        query=query_str,
    )
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="update")
@click.argument(
    "access_condition_id",
    nargs=1,
    required=True,
    type=click.STRING,
    shell_complete=completion.acl_ids,
)
@click.option(
    "--name",
    "name",
    type=click.STRING,
    help=HELP_TEXTS["name"],
)
@click.option(
    "--description",
    "description",
    type=click.STRING,
    help=HELP_TEXTS["description"],
)
@click.option(
    "--user",
    type=click.STRING,
    shell_complete=completion.acl_users,
    help=HELP_TEXTS["user"],
    callback=_value_to_acl_url,
)
@click.option(
    "--group",
    "groups",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.acl_groups,
    help=HELP_TEXTS["group"],
    callback=_list_to_acl_url,
)
@click.option(
    "--read-graph",
    "read_graphs",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.graph_uris_with_all_graph_uri,
    help=HELP_TEXTS["read_graph"],
)
@click.option(
    "--write-graph",
    "write_graphs",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.graph_uris_with_all_graph_uri,
    help=HELP_TEXTS["write_graph"],
)
@click.option(
    "--action",
    "actions",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.acl_actions,
    help=HELP_TEXTS["action"],
)
@click.option(
    "--read-graph-pattern",
    "read_graph_patterns",
    type=click.STRING,
    multiple=True,
    help=HELP_TEXTS["read_graph_pattern"],
)
@click.option(
    "--write-graph-pattern",
    "write_graph_patterns",
    type=click.STRING,
    multiple=True,
    help=HELP_TEXTS["write_graph_pattern"],
)
@click.option(
    "--action-pattern",
    "action_patterns",
    type=click.STRING,
    multiple=True,
    help=HELP_TEXTS["action_pattern"],
)
@click.option(
    "--query",
    "query",
    type=click.STRING,
    shell_complete=completion.remote_queries_and_sparql_files,
    help=HELP_TEXTS["query"],
)
@click.pass_obj
def update_command(  # noqa: PLR0913
    app: ApplicationContext,
    access_condition_id: str,
    name: str,
    description: str,
    user: str,
    groups: list[str],
    read_graphs: tuple[str],
    write_graphs: tuple[str],
    actions: tuple[str],
    read_graph_patterns: tuple[str],
    write_graph_patterns: tuple[str],
    action_patterns: tuple[str],
    query: str,
) -> None:
    """Update an access condition.

    Given an access condition URL, you can change specific options
    to new values.
    """
    iri = convert_qname_to_iri(qname=access_condition_id, default_ns=NS_ACL)
    payload = get_access_condition_by_iri(iri=iri).json()
    app.echo_info(
        f"Updating access condition {payload['name']} ... ",
        nl=False,
    )
    query_str = None
    if query:
        query_str = get_query_text(query, {"user", "group", "readGraph", "writeGraph"})

    update_access_condition(
        iri=iri,
        name=name,
        description=description,
        user=user,
        groups=groups,
        read_graphs=read_graphs,
        write_graphs=write_graphs,
        actions=[convert_qname_to_iri(qname=_, default_ns=NS_ACTION) for _ in actions],
        read_graph_patterns=read_graph_patterns,
        write_graph_patterns=write_graph_patterns,
        action_patterns=action_patterns,
        query=query_str,
    )
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="delete")
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    help=acl_list.get_filter_help_text(),
    shell_complete=acl_list.complete_values,
    multiple=True,
)
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Delete all access conditions. " "This is a dangerous option, so use it with care.",
)
@click.argument(
    "access_condition_ids",
    nargs=-1,
    type=click.STRING,
    shell_complete=completion.acl_ids,
)
@click.pass_context
def delete_command(
    ctx: Context, access_condition_ids: tuple[str], filter_: tuple[tuple[str, str]], all_: bool
) -> None:
    """Delete access conditions.

    This command deletes existing access conditions from the account.

    Warning: Access conditions will be deleted without prompting.

    Note: Access conditions can be listed by using the `admin acl list` command.
    """
    app: ApplicationContext = ctx.obj

    # Validation: require at least one selection method
    if not access_condition_ids and not filter_ and not all_:
        raise click.UsageError(
            "Either provide at least one access condition ID, a filter, or use the --all flag."
        )

    if access_condition_ids and (all_ or filter_):
        raise click.UsageError(
            "Either specify access condition IDs OR use a --filter or the --all option."
        )

    # Get access conditions to delete based on selection method
    acls_to_delete = _get_acls_to_delete(ctx, access_condition_ids, all_, filter_)

    # Avoid double removal as well as sort IRIs
    iris_to_delete = sorted({acl["iri"] for acl in acls_to_delete}, key=lambda v: v.lower())
    count = len(iris_to_delete)

    # Delete each access condition
    for current, iri in enumerate(iris_to_delete, start=1):
        current_string = str(current).zfill(len(str(count)))
        app.echo_info(f"Delete access condition {current_string}/{count}: {iri} ... ", nl=False)
        delete_access_condition(iri=iri)
        app.echo_success("deleted")


@click.command(cls=CmemcCommand, name="export")
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Export all access conditions.",
)
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    help=acl_list.get_filter_help_text(),
    shell_complete=acl_list.complete_values,
    multiple=True,
)
@click.option(
    "--output-file",
    type=ClickSmartPath(writable=True, allow_dash=True, dir_okay=False),
    help="Export to this file. Use '-' for stdout. "
    "If specified, overrides --output-dir and --filename-template.",
)
@click.option(
    "--output-dir",
    default=".",
    show_default=True,
    type=ClickSmartPath(writable=True, file_okay=False),
    help="The base directory, where the ACL files will be created. "
    "If this directory does not exist, it will be silently created. "
    "Ignored if --output-file is specified.",
)
@click.option(
    "--filename-template",
    "-t",
    "template",
    default="{{date}}-{{connection}}.acls.json",
    show_default=True,
    type=click.STRING,
    help="Template for the export file name(s). Possible placeholders are (Jinja2): "
    "{{connection}} (from the --connection option) and "
    "{{date}} (the current date as YYYY-MM-DD). "
    "Needed directories will be created. "
    "Ignored if --output-file is specified.",
)
@click.option(
    "--replace",
    is_flag=True,
    help="Replace existing files. This is a dangerous option, so use it with care.",
)
@click.argument(
    "access_condition_ids",
    nargs=-1,
    type=click.STRING,
    shell_complete=completion.acl_ids,
)
@click.pass_context
def export_command(  # noqa: PLR0913
    ctx: Context,
    all_: bool,
    filter_: tuple[tuple[str, str]],
    output_file: str | None,
    output_dir: str,
    template: str,
    replace: bool,
    access_condition_ids: tuple[str],
) -> None:
    """Export access conditions to a JSON file.

    Access conditions can be exported based on IDs, filters, or all at once.
    The exported JSON can be imported back using the `acl import` command.

    By default, uses template-based file naming with the current date and connection name.
    You can override this by specifying an explicit output file path with --output-file.

    Example: cmemc admin acl export --all

    Example: cmemc admin acl export --all --output-file acls.json

    Example: cmemc admin acl export --filter group local-users

    Example: cmemc admin acl export :my-acl-iri
    """
    app: ApplicationContext = ctx.obj

    if not access_condition_ids and not filter_ and not all_:
        raise click.UsageError(
            "Either provide at least one access condition ID, a filter, or use the --all flag."
        )

    if all_:
        acls_to_export = fetch_all_acls()
    else:
        # Apply user-provided filters first
        filter_to_apply = list(filter_) if filter_ else []

        # If IDs provided, add internal list-of-ids filter (with OR logic)
        if access_condition_ids:
            iris = [convert_qname_to_iri(qname=_, default_ns=NS_ACL) for _ in access_condition_ids]
            filter_to_apply.append(("ids", ",".join(iris)))

        acls_to_export = acl_list.apply_filters(ctx=ctx, filter_=filter_to_apply)

    if not acls_to_export:
        raise click.ClickException("No access conditions found to export.")

    count = len(acls_to_export)
    output = json.dumps(acls_to_export, indent=2)

    # Handle stdout special case early
    if output_file == "-":
        click.echo(output)
        return

    # Determine output path based on mode
    if output_file:
        # Mode 1: Explicit output file (overrides template parameters)
        export_path = output_file
    else:
        # Mode 2: Template-based output (default)
        template_data = app.get_template_data()
        local_name = Template(template).render(template_data)
        export_path = os.path.normpath(str(Path(output_dir) / local_name))
        # Create parent directory if needed (only in template mode)
        Path(export_path).parent.mkdir(exist_ok=True, parents=True)

    # Write to file
    app.echo_info(f"Exporting {count} access condition(s) to {export_path} ... ", nl=False)
    if Path(export_path).exists() and replace is not True:
        app.echo_error("file exists")
        return

    with click.open_file(export_path, "w") as f:
        f.write(output)
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="import")
@click.option(
    "--replace",
    is_flag=True,
    help="Replace existing access conditions with the same IRI. "
    "By default, import will fail if an access condition already exists.",
)
@click.argument(
    "input_file",
    required=True,
    type=ClickSmartPath(readable=True, allow_dash=False, dir_okay=False),
    shell_complete=completion.acl_files,
)
@click.pass_context
def import_command(ctx: Context, replace: bool, input_file: str) -> None:
    """Import access conditions from a JSON file.

    This command imports access conditions from a JSON file that was created
    using the `acl export` command.

    If --replace is specified, existing access conditions with matching IRIs
    will be deleted before importing. Otherwise, the import will skip if an
    access condition with the same IRI already exists.

    Example: cmemc admin acl import acls.json

    Example: cmemc admin acl import --replace acls.json
    """
    app: ApplicationContext = ctx.obj

    # Read and parse JSON file
    try:
        with click.open_file(input_file, "r") as f:
            acls_to_import = json.load(f)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON file: {e}") from e

    if not isinstance(acls_to_import, list):
        raise click.ClickException("JSON file must contain a list of access conditions.")

    if not acls_to_import:
        app.echo_warning("No access conditions found in file.")
        return

    existing_acls = {acl["iri"]: acl for acl in fetch_all_acls()}
    count = len(acls_to_import)
    imported = 0
    skipped = 0

    for current, acl_data in enumerate(acls_to_import, start=1):
        iri = acl_data.get("iri")
        name = acl_data.get("name", "Unnamed")

        if not iri:
            app.echo_warning(f"Skipping ACL {current}/{count}: missing IRI")
            skipped += 1
            continue

        # Extract ID from IRI
        acl_id = iri.split("/")[-1]

        app.echo_info(f"Import ACL {current}/{count}: {name} ({acl_id}) ... ", nl=False)

        # Check if already exists
        if iri in existing_acls:
            if replace:
                app.echo_info("replacing ... ", nl=False)
                delete_access_condition(iri=iri)
            else:
                app.echo_warning("skipped (already exists)")
                skipped += 1
                continue

        # Create the access condition
        create_access_condition(
            name=acl_data.get("name", "Imported ACL"),
            static_id=acl_id,
            description=acl_data.get("comment", "Created with cmemc"),
            user=acl_data.get("requiresAccount"),
            groups=acl_data.get("requiresGroup", []),
            read_graphs=acl_data.get("readableGraphs", []),
            write_graphs=acl_data.get("writableGraphs", []),
            actions=acl_data.get("allowedActions", []),
            read_graph_patterns=acl_data.get("grantReadPatterns", []),
            write_graph_patterns=acl_data.get("grantWritePatterns", []),
            action_patterns=acl_data.get("grantAllowedActions", []),
            query=None,  # Queries not supported in import
        )
        app.echo_success("done")
        imported += 1

    # Summary
    app.echo_info(f"Import complete: {imported} imported, {skipped} skipped")


@click.command(name="review")
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.argument("user", type=click.STRING, shell_complete=completion.acl_users)
@click.option(
    "--group",
    "groups",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.acl_groups,
    callback=_list_to_acl_url,
    help="Add groups to the review request (what-if-scenario).",
)
@click.pass_obj
def review_command(app: ApplicationContext, raw: bool, user: str, groups: list[str] | None) -> None:
    """Review grants for a given account.

    This command has two working modes: (1) You can review the access conditions
    of an actual account,
    (2) You can review the access conditions of an imaginary account with a set of
    freely added groups (what-if-scenario).

    The output of the command is a list of grants the account has based on your input
    and all access conditions loaded in the store. In addition to that, some metadata
    of the account is shown.
    """
    if not groups:
        app.echo_debug("Trying to fetch groups from keycloak.")
        keycloak_user = get_user_by_username(username=user)
        if not keycloak_user:
            if user != PUBLIC_USER_URI:
                app.echo_warning(WARNING_UNKNOWN_USER)
                app.echo_warning(WARNING_USE_GROUP)
        else:
            try:
                keycloak_user_groups = user_groups(user_id=keycloak_user[0]["id"])
                groups = [f"{NS_GROUP}{_['name']}" for _ in keycloak_user_groups]
            except (requests.exceptions.HTTPError, IndexError):
                app.echo_warning(WARNING_NO_GROUP_ACCESS)
                app.echo_warning(WARNING_USE_GROUP)
    app.echo_debug(f"Got groups: {groups}")
    account_iri = f"{NS_USER}{user}" if user != PUBLIC_USER_URI else PUBLIC_USER_URI
    review_info: dict = review_graph_rights(account_iri=account_iri, group_iris=groups).json()
    review_info["groupIri"] = groups
    if raw:
        app.echo_info_json(review_info)
        return
    table = struct_to_table(review_info)
    app.echo_info_table(table, headers=["Key", "Value"], sort_column=0)


@click.group(cls=CmemcGroup)
def acl() -> CmemcGroup:  # type: ignore[empty-body]
    """List, create, delete and modify and review access conditions.

    With this command group, you can manage and inspect access conditions
    in eccenca Corporate Memory. Access conditions are identified by a URL.
    They grant access to knowledge graphs or actions to user or groups.
    """


acl.add_command(list_command)
acl.add_command(inspect_command)
acl.add_command(create_command)
acl.add_command(update_command)
acl.add_command(delete_command)
acl.add_command(export_command)
acl.add_command(import_command)
acl.add_command(review_command)
