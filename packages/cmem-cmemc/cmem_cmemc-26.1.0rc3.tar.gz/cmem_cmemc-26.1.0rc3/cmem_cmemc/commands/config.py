"""configuration commands for cmem command line interface."""

import click
from click import Context

from cmem_cmemc.command import CmemcCommand
from cmem_cmemc.command_group import CmemcGroup
from cmem_cmemc.context import KNOWN_CONFIG_KEYS, ApplicationContext, build_caption
from cmem_cmemc.exceptions import CmemcError
from cmem_cmemc.object_list import (
    DirectValuePropertyFilter,
    ObjectList,
    compare_regex,
)


def get_connections(ctx: Context) -> list[dict]:
    """Get connections for object list"""
    app = ctx.obj
    if app is not None:
        config = app.get_config()
    else:
        # when in completion mode, obj is not set :-(
        # return empty list
        return []

    connections = []

    for section_name in config.sections():
        if section_name != "DEFAULT":
            section = config[section_name]
            connections.append(
                {
                    "name": section_name,
                    "base_uri": section.get("CMEM_BASE_URI", "-"),
                    "grant_type": section.get("OAUTH_GRANT_TYPE", "-"),
                }
            )

    return connections


config_list = ObjectList(
    name="connections",
    get_objects=get_connections,
    filters=[
        DirectValuePropertyFilter(
            name="regex",
            description="Filter by regex matching the connection name.",
            property_key="name",
            compare=compare_regex,
            completion_method="none",
        ),
    ],
)


@click.command(cls=CmemcCommand, name="list")
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    multiple=True,
    help=config_list.get_filter_help_text(),
    shell_complete=config_list.complete_values,
)
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only connection names. "
    "This is useful for piping the names into other cmemc commands.",
)
@click.pass_context
def list_command(ctx: Context, filter_: tuple[tuple[str, str]], id_only: bool) -> None:
    """List configured connections.

    This command lists all configured connections from the currently used config file.
    Each connection is listed with its name, base URI, and grant type.

    The connection identifier can be used with the --connection option
    in order to use a specific Corporate Memory instance.

    You can use the --filter option to filter connections by regex matching
    the connection name.

    In order to apply commands on more than one instance, you need to use
    typical unix gear such as xargs or parallel.

    Example: cmemc config list

    Example: cmemc config list --id-only | xargs -I % sh -c 'cmemc -c % admin status'

    Example: cmemc config list --id-only | parallel --jobs 5 cmemc -c {} admin status
    """
    app = ctx.obj
    connections = config_list.apply_filters(ctx=ctx, filter_=filter_)

    # Sort connections case-insensitively by name
    connections = sorted(connections, key=lambda c: c["name"].casefold())

    if id_only:
        for connection in connections:
            app.echo_result(connection["name"])
        return

    table = [
        (
            connection["name"],
            connection["base_uri"],
            connection["grant_type"],
        )
        for connection in connections
    ]

    filtered = len(filter_) > 0
    app.echo_info_table(
        table,
        headers=["Connection", "Base URI", "Grant Type"],
        caption=build_caption(
            len(table), "connection", instance=str(app.config_file), filtered=filtered
        ),
        empty_table_message="No connections found for these filters."
        if filtered
        else "No connections found.",
    )


@click.command(cls=CmemcCommand, name="edit")
@click.pass_obj
def edit_command(app: ApplicationContext) -> None:
    """Edit the user-scope configuration file."""
    app.echo_info("Open editor for config file " + str(app.config_file))
    click.edit(filename=str(app.config_file))


@click.command(cls=CmemcCommand, name="get")
@click.argument(
    "KEY", nargs=1, type=click.Choice(list(KNOWN_CONFIG_KEYS.keys()), case_sensitive=False)
)
@click.pass_obj
def get_command(app: ApplicationContext, key: str) -> None:
    """Get the value of a known cmemc configuration key.

    In order to automate processes such as fetching custom API data
    from multiple Corporate Memory instances, this command provides a way to
    get the value of a cmemc configuration key for the selected deployment.

    Example: curl -H "Authorization: Bearer $(cmemc -c my admin token)"
    $(cmemc -c my config get DP_API_ENDPOINT)/api/custom/slug

    The commands return with exit code 1 if the config key is not used in
    the current configuration.
    """
    value = KNOWN_CONFIG_KEYS[key]()
    app.echo_debug(f"Type of {key} value is {type(value)}")
    if value is None:
        raise CmemcError(f"Configuration key {key} is not used in this configuration.")
    app.echo_info(str(value))


@click.command(cls=CmemcCommand, name="eval")
@click.option(
    "--unset",
    is_flag=True,
    help="Instead of exporting all configuration keys, " "this option will unset all keys.",
)
@click.pass_obj
def eval_command(app: ApplicationContext, unset: bool) -> None:
    """Export all configuration values of a configuration for evaluation.

    The output of this command is suitable to be used by a shell's `eval`
    command. It will output the complete configuration as `export key="value"`
    statements, which allow for the preparation of a shell environment.

    Example: eval $(cmemc -c my config eval)

    Warning: Please be aware that credential details are shown in cleartext
    with this command.
    """
    for key in sorted(KNOWN_CONFIG_KEYS):
        if unset:
            app.echo_info(f"unset {key!s}")
        else:
            value = KNOWN_CONFIG_KEYS[key]()
            if value is None or value == "None":
                app.echo_info(f"unset {key!s}")
            else:
                app.echo_info(f'export {key!s}="{value}"')


@click.group(cls=CmemcGroup)
def config() -> CmemcGroup:  # type: ignore[empty-body]
    """List and edit configs as well as get config values.

    Configurations are identified by the section identifier in the
    config file. Each configuration represent a Corporate Memory deployment
    with its specific access method as well as credentials.

    A minimal configuration which uses client credentials has the following
    entries:

    \b
    [example.org]
    CMEM_BASE_URI=https://cmem.example.org/
    OAUTH_GRANT_TYPE=client_credentials
    OAUTH_CLIENT_ID=cmem-service-account
    OAUTH_CLIENT_SECRET=my-secret-account-pass

    Note that OAUTH_GRANT_TYPE can be either client_credentials, password or
    prefetched_token.

    In addition to that, the following config parameters can be used as well:

    \b
    SSL_VERIFY=False    - for ignoring certificate issues (not recommended)
    DP_API_ENDPOINT=URL - to point to a non-standard Explore backend (DataPlatform) location
    DI_API_ENDPOINT=URL - to point to a non-standard Build (DataIntegration) location
    OAUTH_TOKEN_URI=URL - to point to an external IdentityProvider location
    OAUTH_USER=username - only if OAUTH_GRANT_TYPE=password
    OAUTH_PASSWORD=password - only if OAUTH_GRANT_TYPE=password
    OAUTH_ACCESS_TOKEN=token - only if OAUTH_GRANT_TYPE=prefetched_token

    In order to get credential information from an external process, you can
    use the parameter OAUTH_PASSWORD_PROCESS, OAUTH_CLIENT_SECRET_PROCESS and
    OAUTH_ACCESS_TOKEN_PROCESS to set up an external executable.

    \b
    OAUTH_CLIENT_SECRET_PROCESS=/path/to/getpass.sh
    OAUTH_PASSWORD_PROCESS=["getpass.sh", "parameter1", "parameter2"]

    The credential executable can use the cmemc environment for fetching the
    credential (e.g. CMEM_BASE_URI and OAUTH_USER).
    If the credential executable is not given with a full path, cmemc
    will look into your environment PATH for something which can be executed.
    The configured process needs to return the credential on the first line
    of stdout. In addition to that, the process needs to exit with exit
    code 0 (without failure). There are examples available in the online
    manual.
    """  # noqa: D301


config.add_command(list_command)
config.add_command(edit_command)
config.add_command(get_command)
config.add_command(eval_command)
