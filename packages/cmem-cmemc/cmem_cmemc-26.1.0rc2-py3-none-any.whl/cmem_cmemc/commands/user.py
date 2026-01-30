"""Keycloak user management commands"""

import sys
from getpass import getpass

import click
from cmem.cmempy.config import get_keycloak_base_uri, get_keycloak_realm_id
from cmem.cmempy.keycloak.group import list_groups
from cmem.cmempy.keycloak.user import (
    assign_groups,
    create_user,
    delete_user,
    get_user_by_username,
    list_users,
    request_password_change,
    reset_password,
    unassign_groups,
    update_user,
    user_groups,
)

from cmem_cmemc import completion
from cmem_cmemc.command import CmemcCommand
from cmem_cmemc.command_group import CmemcGroup
from cmem_cmemc.context import ApplicationContext, build_caption
from cmem_cmemc.exceptions import CmemcError
from cmem_cmemc.object_list import (
    DirectMultiValuePropertyFilter,
    DirectValuePropertyFilter,
    ObjectList,
    compare_regex,
    transform_lower,
)

NO_USER_ERROR = (
    "{} is not a valid user account. Use the 'admin user list' command "
    "to get a list of existing user accounts."
)
EXISTING_USER_ERROR = "{} does already exist"
NO_GROUP_ERROR = "{} is not a valid group. Valid groups are {}"
INVALID_UNASSIGN_GROUP_ERROR = "Group {} is not assigned to user. Valid groups are {}"
NO_EMAIL_ERROR = "Email is empty for {} user."


def get_users(ctx: click.Context) -> list[dict]:  # noqa: ARG001
    """Get users for object list"""
    users: list[dict] = list_users()
    return users


user_list = ObjectList(
    name="users",
    get_objects=get_users,
    filters=[
        DirectValuePropertyFilter(
            name="enabled",
            description="Filter accounts by enabled flag.",
            property_key="enabled",
            transform=transform_lower,
        ),
        DirectValuePropertyFilter(
            name="email",
            description="Filter accounts by regex matching the email address.",
            property_key="email",
            compare=compare_regex,
            fixed_completion=[],
        ),
        DirectValuePropertyFilter(
            name="username",
            description="Filter accounts by regex matching the username.",
            property_key="username",
            compare=compare_regex,
            fixed_completion=[],
        ),
        DirectMultiValuePropertyFilter(
            name="usernames",
            description="Internal filter for multiple usernames.",
            property_key="username",
        ),
    ],
)


def _validate_usernames(usernames: tuple[str, ...]) -> None:
    """Validate that all provided usernames exist."""
    if not usernames:
        return
    all_users = list_users()
    all_usernames = [user["username"] for user in all_users]
    for username in usernames:
        if username not in all_usernames:
            raise CmemcError(NO_USER_ERROR.format(username))


def _get_users_to_delete(
    ctx: click.Context,
    usernames: tuple[str, ...],
    all_: bool,
    filter_: tuple[tuple[str, str], ...],
) -> list[str]:
    """Get the list of usernames to delete based on selection method."""
    if all_:
        # Get all users
        users = list_users()
        return [user["username"] for user in users]

    # Validate provided usernames exist before proceeding
    _validate_usernames(usernames)

    # Build filter list
    filter_to_apply = list(filter_) if filter_ else []

    # Add usernames if provided (using internal multi-value filter)
    if usernames:
        filter_to_apply.append(("usernames", ",".join(usernames)))

    # Apply filters
    users = user_list.apply_filters(ctx=ctx, filter_=filter_to_apply)

    # Build list of usernames
    result = [user["username"] for user in users]

    # Validation: ensure we found users
    if not result and not usernames:
        raise CmemcError("No user accounts found matching the provided filters.")

    return result


@click.command(cls=CmemcCommand, name="list")
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    multiple=True,
    help=user_list.get_filter_help_text(),
    shell_complete=user_list.complete_values,
)
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only username. " "This is useful for piping the IDs into other commands.",
)
@click.pass_context
def list_command(
    ctx: click.Context, filter_: tuple[tuple[str, str]], raw: bool, id_only: bool
) -> None:
    """List user accounts.

    Outputs a list of user accounts, which can be used to get an overview as well
    as a reference for the other commands of the `admin user` command group.
    """
    app = ctx.obj
    users = user_list.apply_filters(ctx=ctx, filter_=filter_)
    if raw:
        app.echo_info_json(users)
        return
    if id_only:
        for usr in users:
            app.echo_info(usr["username"])
        return
    table = [
        (
            usr["username"],
            usr.get("firstName", "-"),
            usr.get("lastName", "-"),
            usr.get("email", "-"),
        )
        for usr in users
    ]
    filtered = len(filter_) > 0
    app.echo_info_table(
        table,
        headers=["Username", "First Name", "Last Name", "Email"],
        sort_column=0,
        caption=build_caption(len(table), "user", filtered=filtered),
        empty_table_message="No user accounts found for these filters."
        if filtered
        else "No user accounts found. Use the `admin user create` command to create an account.",
    )


@click.command(cls=CmemcCommand, name="delete")
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Delete all user accounts. This is a dangerous option, so use it with care.",
)
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    multiple=True,
    shell_complete=user_list.complete_values,
    help=user_list.get_filter_help_text(),
)
@click.argument("usernames", nargs=-1, type=click.STRING, shell_complete=completion.user_ids)
@click.pass_context
def delete_command(
    ctx: click.Context,
    all_: bool,
    filter_: tuple[tuple[str, str]],
    usernames: tuple[str],
) -> None:
    """Delete user accounts.

    This command deletes user accounts from a realm.

    Warning: User accounts will be deleted without prompting.

    Note: The deletion of user accounts does not delete the assigned groups,
    only the assignments to these groups. User accounts can be listed by using
    the `admin user list` command.
    """
    app = ctx.obj

    # Validation: require at least one selection method
    if not usernames and not all_ and not filter_:
        raise click.UsageError(
            "Either specify at least one username"
            " or use a --filter option,"
            " or use the --all option to delete all user accounts."
        )

    if usernames and (all_ or filter_):
        raise click.UsageError("Either specify a username OR use a --filter or the --all option.")

    # Get users to delete based on selection method
    users_to_delete = _get_users_to_delete(ctx, usernames, all_, filter_)

    # Avoid double removal as well as sort usernames
    processed_usernames = sorted(set(users_to_delete), key=lambda v: v.lower())
    count = len(processed_usernames)

    # Delete each user
    for current, username in enumerate(processed_usernames, start=1):
        current_string = str(current).zfill(len(str(count)))
        app.echo_info(f"Delete user {current_string}/{count}: {username} ... ", nl=False)
        users = get_user_by_username(username)
        if not users:
            raise CmemcError(NO_USER_ERROR.format(username))
        delete_user(users[0]["id"])
        app.echo_success("deleted")


@click.command(cls=CmemcCommand, name="create")
@click.argument("username")
@click.pass_obj
def create_command(app: ApplicationContext, username: str) -> None:
    """Create a user account.

    This command creates a new user account.

    Note: The created user account has no metadata such as personal data or group
    assignments. In order to add these details to a user account, use the
    `admin user update` command.
    """
    app.echo_info(f"Creating user {username} ... ", nl=False)
    users = get_user_by_username(username)
    if users:
        raise CmemcError(EXISTING_USER_ERROR.format(username))

    create_user(username=username)
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="update")
@click.argument("username", shell_complete=completion.user_ids)
@click.option("--first-name", type=click.STRING, required=False, help="Set a new first name.")
@click.option("--last-name", type=click.STRING, required=False, help="Set a new last name.")
@click.option("--email", type=click.STRING, required=False, help="Set a new email.")
@click.option(
    "--assign-group",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.user_group_ids,
    help="Assign a group.",
)
@click.option(
    "--unassign-group",
    type=click.STRING,
    multiple=True,
    shell_complete=completion.user_group_ids,
    help="Unassign a group.",
)
@click.pass_obj
def update_command(  # noqa: PLR0913
    app: ApplicationContext,
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    assign_group: tuple[str, ...],
    unassign_group: tuple[str, ...],
) -> None:
    """Update a user account.

    This command updates metadata and group assignments of a user account.

    For each data value, a separate option needs to be used. All options can
    be combined in a single execution.

    Note: In order to assign a group to a user account, the group need to be
    added or imported to the realm upfront.
    """
    options = (first_name, last_name, email, assign_group, unassign_group)
    if all(_ is None or _ == () for _ in options):
        raise click.UsageError(
            "This commands needs to be used with at least one option "
            "(e.g. --email). See the command help for a list of options."
        )
    app.echo_info(f"Updating user {username} ... ", nl=False)
    users = get_user_by_username(username)
    if not users:
        raise CmemcError(NO_USER_ERROR.format(username))
    user_id = users[0]["id"]
    all_groups = {group["name"]: group["id"] for group in list_groups()}
    invalid_groups = [group for group in assign_group if group not in all_groups]
    existing_user_groups = {group["name"] for group in user_groups(user_id)}

    if invalid_groups:
        raise CmemcError(
            NO_GROUP_ERROR.format(
                ", ".join(invalid_groups), ", ".join(all_groups.keys() - set(existing_user_groups))
            )
        )

    invalid_unassign_groups = [
        group for group in unassign_group if group not in existing_user_groups
    ]
    if invalid_unassign_groups:
        raise CmemcError(
            INVALID_UNASSIGN_GROUP_ERROR.format(
                ", ".join(invalid_unassign_groups), ", ".join(existing_user_groups)
            )
        )

    assign_group_ids = [all_groups[name] for name in assign_group]
    unassign_groups_ids = [all_groups[name] for name in unassign_group]
    unassign_groups(user_id, unassign_groups_ids)
    assign_groups(user_id, assign_group_ids)

    update_user(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        email_verified=True if email else None,
    )
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="password")
@click.argument("username", shell_complete=completion.user_ids)
@click.option(
    "--value", help="With this option, the new password can be set in a non-interactive way."
)
@click.option(
    "--temporary", is_flag=True, help="If enabled, the user must change the password on next login."
)
@click.option(
    "--request-change",
    is_flag=True,
    help="If enabled, will send a email to user to reset the password.",
)
@click.pass_obj
def password_command(
    app: ApplicationContext, username: str, value: str, temporary: bool, request_change: bool
) -> None:
    """Change the password of a user account.

    With this command, the password of a user account can be changed.
    The default execution mode of this command is an interactive prompt which asks
    for the password (twice). In order automate password changes, you can use the
    `--value` option.

    Warning: Providing passwords on the command line can be dangerous
    (e.g. due to a potential exploitation in the shell history).
    A suggested more save way for automation is to provide the password in a variable
    first (e.g. with `NEW_PASS=$(pwgen -1 40)`) and use it afterward in the
    cmemc call: `cmemc admin user password max --value ${NEW_PASS}`.
    """
    app.echo_info(f"Changing password for account {username} ... ", nl=False)
    users = get_user_by_username(username)
    if not users:
        raise CmemcError(NO_USER_ERROR.format(username))
    if not value and not request_change:
        app.echo_info("\nNew password: ", nl=False)
        value = getpass(prompt="")
        app.echo_info("Retype new password: ", nl=False)
        retype_password = getpass(prompt="")
        if value != retype_password:
            app.echo_error("Sorry, passwords do not match.")
            app.echo_error("password unchanged")
            sys.exit(1)
    if value:
        reset_password(user_id=users[0]["id"], value=value, temporary=temporary)
    if request_change and not users[0].get("email", None):
        raise CmemcError(NO_EMAIL_ERROR.format(username))
    if request_change:
        request_password_change(users[0]["id"])
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="open")
@click.argument(
    "usernames", nargs=-1, required=False, type=click.STRING, shell_complete=completion.user_ids
)
@click.pass_obj
def open_command(app: ApplicationContext, usernames: str) -> None:
    """Open user in the browser.

    With this command, you can open a user in the keycloak console in
    your browser to change them.

    The command accepts multiple usernames which results in
    opening multiple browser tabs.
    """
    open_user_base_uri = (
        f"{get_keycloak_base_uri()}/admin/master/console/#/" f"{get_keycloak_realm_id()}/users"
    )
    if not usernames:
        app.echo_debug(f"Open users list: {open_user_base_uri}")
        click.launch(open_user_base_uri)
    else:
        users = list_users()
        user_name_id_map = {u["username"]: u["id"] for u in users}
        for _ in usernames:
            if _ not in user_name_id_map:
                raise CmemcError(NO_USER_ERROR.format(_))
            user_id = user_name_id_map[_]
            open_user_uri = f"{open_user_base_uri}/{user_id}/settings"

            app.echo_debug(f"Open {_}: {open_user_uri}")
            click.launch(open_user_uri)


@click.group(cls=CmemcGroup)
def user() -> CmemcGroup:  # type: ignore[empty-body]
    """List, create, delete and modify user accounts.

    This command group is an opinionated interface to the Keycloak realm of your
    Corporate Memory instance. In order to be able to manage user data, the
    configured cmemc connection account needs to be equipped with the
    `manage-users` role in the used realm.

    User accounts are identified by a username which unique in the scope of
    the used realm.

    In case your Corporate Memory deployment does not use the default deployment
    layout, the following additional config variables can be used in your
    connection configuration: `KEYCLOAK_BASE_URI` defaults to
    `/auth` on `CMEM_BASE_URI` and locates your Keycloak deployment;
    `KEYCLOAK_REALM_ID` defaults to `cmem` and identifies the used realm.
    """


user.add_command(list_command)
user.add_command(create_command)
user.add_command(update_command)
user.add_command(delete_command)
user.add_command(password_command)
user.add_command(open_command)
