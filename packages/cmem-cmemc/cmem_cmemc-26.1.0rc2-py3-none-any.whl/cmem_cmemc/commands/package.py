"""Package command group"""

import json
import os
from pathlib import Path

import click
import requests
from click.shell_completion import CompletionItem
from cmem_client.client import Client
from cmem_client.repositories.marketplace_packages import (
    MarketplacePackagesExportConfig,
    MarketplacePackagesImportConfig,
    MarketplacePackagesRepository,
)
from eccenca_marketplace_client.package_version import PackageVersion
from pydantic_extra_types.semantic_version import SemanticVersion

from cmem_cmemc import completion
from cmem_cmemc.command import CmemcCommand
from cmem_cmemc.command_group import CmemcGroup
from cmem_cmemc.completion import suppress_completion_errors
from cmem_cmemc.context import ApplicationContext
from cmem_cmemc.exceptions import CmemcError
from cmem_cmemc.object_list import (
    DirectValuePropertyFilter,
    ObjectList,
    compare_regex,
    compare_str_equality,
)
from cmem_cmemc.parameter_types.path import ClickSmartPath
from cmem_cmemc.utils import struct_to_table


def get_installed_packages_list(ctx: click.Context) -> list[dict]:
    """Get the list of installed packages"""
    ApplicationContext.set_connection_from_params(ctx.find_root().params)
    client = Client.from_cmempy()
    packages: MarketplacePackagesRepository = client.marketplace_packages
    return [
        {
            "id": package_.package_version.manifest.package_id,
            "type": str(package_.package_version.manifest.package_type).replace(
                "PackageTypes.", ""
            ),
            "version": str(package_.package_version.manifest.package_version),
            "name": package_.package_version.manifest.metadata.name,
            "description": package_.package_version.manifest.metadata.description,
        }
        for package_ in packages.values()
    ]


installed_packages_list = ObjectList(
    name="installed packages",
    get_objects=get_installed_packages_list,
    filters=[
        DirectValuePropertyFilter(
            name="type",
            description="Filter list by package type.",
            property_key="type",
        ),
        DirectValuePropertyFilter(
            name="name",
            description="Filter list by regex matching the package name.",
            property_key="name",
            compare=compare_regex,
            fixed_completion=[],
        ),
        DirectValuePropertyFilter(
            name="id",
            description="Filter list by package ID.",
            property_key="id",
            compare=compare_str_equality,
        ),
    ],
)


@suppress_completion_errors
def _complete_installed_package_ids(
    ctx: click.Context,
    param: click.Argument,  # noqa: ARG001
    incomplete: str,
) -> list[CompletionItem]:
    """Prepare a list of IDs of installed packages."""
    ApplicationContext.set_connection_from_params(ctx.find_root().params)
    candidates = [
        (_["id"], f"{_['version']}: {_['name']}")
        for _ in installed_packages_list.apply_filters(ctx=ctx)
    ]
    return completion.finalize_completion(candidates=candidates, incomplete=incomplete)


@click.command(cls=CmemcCommand, name="inspect")
@click.argument(
    "PACKAGE_PATH",
    required=True,
    type=ClickSmartPath(
        allow_dash=False,
        dir_okay=True,
        readable=True,
        exists=True,
        remote_okay=True,
    ),
)
@click.option(
    "--key",
    "key",
    help="Get a specific key only from the manifest.",
)
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.pass_obj
def inspect_command(app: ApplicationContext, package_path: Path, key: str, raw: str) -> None:
    """Inspect the manifest of a package."""
    path = Path(package_path)
    package_version = (
        PackageVersion.from_directory(path, validate_files=False)
        if path.is_dir()
        else PackageVersion.from_archive(path)
    )
    manifest = package_version.manifest
    manifest_data = json.loads(manifest.model_dump_json(indent=2))
    if raw:
        app.echo_info_json(manifest_data)
        return
    if key:
        table = [
            line
            for line in struct_to_table(manifest_data)
            if line[0].startswith(key) or key == "all"
        ]
        if len(table) == 1:
            app.echo_info(table[0][1])
            return
        if len(table) == 0:
            raise CmemcError(f"No values for key '{key}'.")
        app.echo_info_table(table, headers=["Key", "Value"], sort_column=0)
        return
    table = struct_to_table(manifest_data)
    app.echo_info_table(
        table,
        headers=["Key", "Value"],
        sort_column=0,
        caption=f"Manifest of package '{manifest.package_id}' in"
        f" {path.name} (v{manifest.package_version})",
    )


@click.command(cls=CmemcCommand, name="list")
@click.option(
    "--filter",
    "filter_",
    multiple=True,
    type=(str, str),
    shell_complete=installed_packages_list.complete_values,
    help=installed_packages_list.get_filter_help_text(),
)
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only package IDs. This is useful for piping the IDs into other commands.",
)
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.pass_context
def list_command(
    ctx: click.Context, filter_: tuple[tuple[str, str]], id_only: bool, raw: bool
) -> None:
    """List installed packages."""
    app: ApplicationContext = ctx.obj
    data = installed_packages_list.apply_filters(ctx=ctx, filter_=filter_)
    if id_only:
        for _ in sorted(data, key=lambda _: _["id"]):
            app.echo_info(_["id"])
        return
    if raw:
        app.echo_info_json(data)
        return
    table = [
        (
            _["id"],
            _["version"],
            _["type"],
            _["name"],
        )
        for _ in data
    ]
    app.echo_info_table(
        table,
        headers=["ID", "Version", "Type", "Name"],
        sort_column=0,
        empty_table_message="No installed packages found. "
        "You can use the `package install` command to install packages.",
    )


@click.command(cls=CmemcCommand, name="install")
@click.argument(
    "PACKAGE_ID",
    required=False,
    type=click.STRING,
)
@click.option(
    "--input",
    "-i",
    "input_path",
    type=ClickSmartPath(allow_dash=False, dir_okay=True, file_okay=True, readable=True),
    help="Install a package from a package archive (.cpa) or directory.",
)
@click.option(
    "--replace", is_flag=True, help="Replace (overwrite) existing package version, if present."
)
@click.pass_obj
def install_command(
    app: ApplicationContext, package_id: str, replace: bool, input_path: str
) -> None:
    """Install packages.

    This command installs a package either from the marketplace or from local package
    archives (.cpa) or directories.
    """
    if not package_id and not input_path:
        raise CmemcError(
            "Nothing to install. Either specify a package ID from the marketplace, "
            "or use the `--input` option to install a local package."
        )
    if package_id and input_path:
        raise CmemcError(
            "You can not install from the marketplace and local files at the same time."
        )

    packages = app.client.marketplace_packages
    if input_path:
        package_path = Path(input_path)
        package_version = (
            PackageVersion.from_directory(package_path, validate_files=False)
            if package_path.is_dir()
            else PackageVersion.from_archive(package_path)
        )
        package_id = package_version.manifest.package_id
        app.echo_info(f"Installing package '{package_id}' from '{input_path}' ... ", nl=False)
        packages.import_item(
            path=package_path,
            replace=replace,
            configuration=MarketplacePackagesImportConfig(install_from_marketplace=False),
        )
    else:
        app.echo_info(f"Installing package '{package_id}' from marketplace ... ", nl=False)
        packages.import_item(key=package_id, replace=replace)
    app.echo_success("done")


def _filter_installed_packages(
    ctx: click.Context, package_id: str | None, filter_: tuple[tuple[str, str]], all_: bool
) -> list[dict]:
    """Filter installed packages."""
    if package_id is None and not filter_ and not all_:
        raise click.UsageError("Either provide a package ID or a filter, or use the --all flag.")

    if all_:
        packages_to_work_on = installed_packages_list.apply_filters(ctx=ctx)
    else:
        filter_to_apply = list(filter_) if filter_ else []
        if package_id:
            filter_to_apply.append(("id", package_id))
        packages_to_work_on = installed_packages_list.apply_filters(
            ctx=ctx, filter_=filter_to_apply
        )

    if not packages_to_work_on and package_id:
        raise CmemcError(f"Package '{package_id}' is not installed.")
    return packages_to_work_on


@click.command(cls=CmemcCommand, name="uninstall")
@click.argument(
    "PACKAGE_ID",
    type=click.STRING,
    shell_complete=_complete_installed_package_ids,
    required=False,
)
@click.option(
    "--filter",
    "filter_",
    multiple=True,
    type=(str, str),
    shell_complete=installed_packages_list.complete_values,
    help=installed_packages_list.get_filter_help_text(),
)
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Uninstall all packages. This is a dangerous option, so use it with care.",
)
@click.pass_context
def uninstall_command(
    ctx: click.Context,
    package_id: str | None,
    filter_: tuple[tuple[str, str]],
    all_: bool,
) -> None:
    """Uninstall installed packages."""
    app: ApplicationContext = ctx.obj
    packages_to_uninstall = _filter_installed_packages(
        ctx=ctx, package_id=package_id, filter_=filter_, all_=all_
    )
    packages = app.client.marketplace_packages
    for _ in packages_to_uninstall:
        id_to_uninstall = _["id"]
        app.echo_info(f"Uninstalling package {id_to_uninstall} ... ", nl=False)
        packages.delete_item(id_to_uninstall)
        app.echo_success("done")


@click.command(cls=CmemcCommand, name="export")
@click.argument(
    "PACKAGE_ID",
    type=click.STRING,
    shell_complete=_complete_installed_package_ids,
    required=False,
)
@click.option(
    "--filter",
    "filter_",
    multiple=True,
    type=(str, str),
    shell_complete=installed_packages_list.complete_values,
    help=installed_packages_list.get_filter_help_text(),
)
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Export all installed packages.",
)
@click.option("--replace", is_flag=True, help="Replace (overwrite) existing files, if present.")
@click.pass_context
def export_command(
    ctx: click.Context,
    package_id: str | None,
    filter_: tuple[tuple[str, str]],
    all_: bool,
    replace: bool,
) -> None:
    """Export installed packages to package directories."""
    app: ApplicationContext = ctx.obj
    packages_to_export = _filter_installed_packages(
        ctx=ctx, package_id=package_id, filter_=filter_, all_=all_
    )
    packages = app.client.marketplace_packages
    for _ in packages_to_export:
        id_to_export = _["id"]
        app.echo_info(f"Exporting package `{id_to_export}` ... ", nl=False)
        configuration = MarketplacePackagesExportConfig(export_as_zip=False)
        packages.export_item(
            id_to_export,
            path=Path(id_to_export),
            replace=replace,
            configuration=configuration,
        )
        app.echo_success("done")


@click.command(cls=CmemcCommand, name="build")
@click.argument(
    "PACKAGE_DIRECTORY",
    required=True,
    type=ClickSmartPath(
        allow_dash=False,
        dir_okay=True,
        file_okay=False,
        readable=True,
        exists=True,
        remote_okay=False,
    ),
)
@click.option("--version", help="Set the package version.")
@click.option("--replace", is_flag=True, help="Replace package archive, if present.")
@click.option(
    "--output-dir",
    type=ClickSmartPath(writable=True, file_okay=False, dir_okay=True),
    help="Create the package archive in a specific directory.",
    default=".",
    show_default=True,
)
@click.pass_obj
def build_command(
    app: ApplicationContext, package_directory: str, version: str, replace: bool, output_dir: str
) -> None:
    """Build a package archive from a package directory.

    This command processes a package directory, validates its content including the manifest,
    and creates a versioned Corporate Memory package archive (.cpa) with the following naming
    convention: {package_id}-v{version}.cpa

    Package archives can be published to the marketplace using the `package publish` command.
    """
    package_path = Path(package_directory)
    package_version = PackageVersion.from_directory(package_path, validate_files=False)
    if version:
        if version.startswith("v"):
            version = version[1:]
        package_version.manifest.package_version = SemanticVersion.parse(version)
    version_str = str(package_version.manifest.package_version)
    package_id = package_version.manifest.package_id

    if output_dir is not None:
        cpa_file = Path(
            os.path.normpath(str(Path(output_dir) / f"{package_id}-v{version_str}.cpa"))
        )
    else:
        cpa_file = Path(f"{package_id}-v{version_str}.cpa")

    Path(cpa_file).parent.mkdir(exist_ok=True, parents=True)

    if version_str.endswith("dirty"):
        app.echo_warning(
            "Dirty Repository: Your version string ends with 'dirty'."
            "This indicates an unclean repository."
        )
    if version_str == "0.0.0":
        raise CmemcError(
            "Invalid Version 0.0.0: "
            "Use the --version option to override this, or change the manifest."
        )
    if cpa_file.exists() and not replace:
        raise CmemcError(
            f"Package archive `{cpa_file}` already exists. Use `--replace` to overwrite."
        )
    app.echo_info(f"Building package archive `{cpa_file.name}` ... ", nl=False)
    package_version.validate_text_files(package_version.manifest, package_path)
    package_version.validate_image_files(package_version.manifest, package_path)
    package_version.build_archive(archive=cpa_file)
    app.echo_success("done")


@click.command(cls=CmemcCommand, name="publish")
@click.argument(
    "PACKAGE_ARCHIVE",
    required=True,
    type=ClickSmartPath(
        allow_dash=False,
        dir_okay=False,
        readable=True,
        exists=True,
        remote_okay=True,
    ),
)
@click.option(
    "--marketplace-url",
    type=str,
    help="Alternative Marketplace URL.",
    default="https://marketplace.eccenca.dev/",
)
@click.pass_obj
def publish_command(app: ApplicationContext, package_archive: str, marketplace_url: str) -> None:
    """Publish a package archive to the marketplace server."""
    package_path = Path(package_archive)

    package_version = PackageVersion.from_archive(package_path)
    package_id = package_version.manifest.package_id

    app.echo_info(f"Publishing package `{package_id}` ... ", nl=False)
    package_data = package_path.read_bytes()
    filename = package_path.name

    if marketplace_url.endswith("/"):
        marketplace_url = marketplace_url[:-1]

    files = {"archive": (filename, package_data, "application/octet-stream")}
    url = f"{marketplace_url}/api/packages/{package_id}/versions"
    response = requests.post(
        url=url,
        timeout=30,
        files=files,
        headers={"accept": "application/json"},
    )

    response.raise_for_status()
    app.echo_success("done")


@click.group(cls=CmemcGroup)
def package_group() -> CmemcGroup:  # type: ignore[empty-body]
    """List, (un)install, export, create, or inspect packages."""


package_group.add_command(inspect_command)
package_group.add_command(list_command)
package_group.add_command(install_command)
package_group.add_command(uninstall_command)
package_group.add_command(export_command)
package_group.add_command(build_command)
package_group.add_command(publish_command)
