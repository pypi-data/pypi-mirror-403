import hashlib
import json
import os.path
import pathlib
import sys

import click
import docker
import packaging
from delta.core import DeltaCore
from delta.manifest.manifest import check_manifest
from packaging.version import parse, InvalidVersion, Version
from rich.live import Live
from rich.text import Text

import delta
from delta.cli.components.template.manifest import Manifest
from delta.cli.utils import API, Utils


@click.command(
    'publish',
    short_help='Publish a DeltaTwin® component to the store'
)
@click.option(
    '--visibility',
    '-v',
    type=click.Choice(['public', 'private']),
    default='private',
    help='Set the visibility of the DeltaTwin®, by default it is private. '
         'Access to this functionality is restricted to administrator.'
)
@click.option(
    '--topic',
    '-t',
    type=str,
    default=None,
    multiple=True,
    help="""Define each topic of the DeltaTwin®
            (multiple topics can be defined)"""
)
@click.option(
    '--change-log',
    '-C',
    type=str,
    default='',
    help='Describe the change log of the DeltaTwin®'
)
@click.option(
    '--conf',
    '-c',
    type=str,
    default=None,
    help='Path to the conf file'
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="If enabled, do not use cache during build phase"
)
@click.help_option("--help", "-h")
@click.argument('version', type=str)
def publish_dt(
        version,
        visibility,
        topic,
        change_log,
        conf,
        no_cache
):
    """Publish a new version of a DeltaTwin® component to the platform.

    \b
    NOTES:
    \b
    🛈 DeltaTwin® components are only visible to the individual user and
    cannot be shared with other users. To make a component publicly accessible,
    please contact DestinE Platform Support.
    \b
    🛈 This command must be executed on the directory of the DeltaTwin
    \b
    🛈 DeltaTwin® names must be unique. A DeltaTwin cannot be published
    if its name is already in use
    \b
    🛈 The characters allowed for naming a DeltaTwin® are letters (a-z)
    digits (0-9) and special (-). Upper case letter are not supported.
    \b
    🛈 Please note that, for public DeltaTwin® componsant, the topic
    ‘starter-kit’ is reserved for the administrator only.

    \b
    MANDATORY ARGUMENT:
    VERSION: identifier of the published DeltaTwin.

    The canonical public version identifiers
    MUST comply with the following scheme:
    [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
    """

    # Parse the version number
    try:
        version: Version = packaging.version.parse(version)
    except InvalidVersion:
        raise click.UsageError(f'Invalid version format: {version}')

    # Ensure the expected files exists
    current_path = os.getcwd()
    manifest_path = pathlib.Path(current_path) / 'manifest.json'
    workflow_path = pathlib.Path(current_path) / 'workflow.yml'
    if not manifest_path.exists() or not workflow_path.exists():
        click.echo(
            f"{Utils.log_error} "
            "Current directory is not a DeltaTwin® component. Please ensure "
            "'manifest.json' and 'workflow.yml' exists."
        )
        sys.exit(1)

    # Load manifest
    try:
        manifest: Manifest = delta.manifest.parser.parse('manifest.json')
        deltatwin_name: str = manifest.name
    except ValueError as ve:
        click.echo(
            f"{Utils.log_error} "
            f"Failed to parse manifest.json : {ve.args[0]}"
        )
        sys.exit(1)

    # Deltatwin does not exist : publish a new one
    if not API.check_dt_exists(conf, deltatwin_name):
        component_data, component_files = prepare_publish(
            conf,
            version=version,
            deltatwin_name=deltatwin_name,
            visibility=visibility,
            topic=topic,
            change_log=change_log,
            path_deltatwin=current_path,
            no_cache=no_cache
        )
        API.publish_dt(conf, component_data, component_files)

    # Component already exists : create a new version
    else:
        existing_deltatwin = API.get_dt(conf, deltatwin_name, param={})
        visibility = existing_deltatwin.get("visibility", None)

        version_data, version_files = prepare_version(
            conf,
            version,
            deltatwin_name,
            current_path,
            change_log,
            visibility,
            no_cache
        )
        del version_data["manifest"]
        print(f"VERSION DATA {version_data}")
        API.publish_version_dt(
            conf, deltatwin_name,
            version_data, version_files
        )

    click.echo(
        f'{Utils.log_info} The DeltaTwin '
        f'{deltatwin_name}-{version}, has been released.'
    )


def prepare_publish(
        conf,
        version,
        deltatwin_name,
        visibility,
        topic,
        change_log,
        path_deltatwin,
        no_cache: bool = False
) -> tuple[dict, dict]:

    topics = []
    for tag_name in topic:
        topics.append(tag_name)

    version_data, version_files = prepare_version(
        conf=conf,
        version=version,
        deltatwin_name=deltatwin_name,
        path_deltatwin=path_deltatwin,
        change_log=change_log,
        visibility=visibility,
        no_cache=no_cache,
    )

    component_data = {
        "visibility": visibility,
        "version": str(version),
        "topics": topics,
        **version_data
    }
    return component_data, version_files


def prepare_version(
        conf,
        version,
        deltatwin_name,
        path_deltatwin,
        change_log,
        visibility,
        no_cache: bool = False
) -> tuple[dict, dict]:

    # Ensure the required files exists
    try:
        manifest_path = os.path.join(path_deltatwin, 'manifest.json')
        with open(manifest_path, 'r') as manifest:
            manifest_data = json.load(manifest)
            if not check_manifest(manifest_data):
                raise click.UsageError(
                    f"{Utils.log_error} Wrong manifest.json"
                )
    except FileNotFoundError:
        raise click.UsageError(f"{Utils.log_error} No manifest.json found")

    workflow_path = os.path.join(path_deltatwin, 'workflow.yml')
    if not os.path.exists(workflow_path):
        raise click.UsageError(f"{Utils.log_error} No workflow.yml found")

    # Check Delta Twin exists with this version
    if API.check_dt_exists(
            conf=conf,
            dt_name=deltatwin_name,
            version=version
    ):
        raise click.UsageError(
            f"The DeltaTwin {deltatwin_name} "
            f"with the version {version} already exists."
        )

    prepare_publish_to_harbor(
        conf,
        version=str(version),
        public=True if visibility == "public" else False,
        no_cache=no_cache,
    )

    data = {
        "version": str(version),
        "changelog": change_log,
        "manifest": manifest_data
    }
    # FIXME in CLI-rewrite : those files are never closed
    files = {
        "manifest": ("manifest.json",
                     open(manifest_path, 'rb'), "application/json"),
        "workflow": ("workflow.yml",
                     open(workflow_path, 'rb'), "application/yaml")
    }

    return data, files


def _push_image_to_registry(
        image_name: str,
        version: str,
        docker_cli,
        auth_config: dict
):
    try:
        resp = docker_cli.api.push(
            image_name,
            tag=version,
            stream=True,
            decode=True,
            auth_config=auth_config
        )

        docker_id = {}

        def get_lines(d: dict):
            lines = [f"{k} : {v}" for k, v in d.items()]
            texts = Text('\n'.join(lines))
            return texts

        with Live(get_lines(docker_id)) as live:
            for line in resp:
                if 'error' in line:
                    raise RuntimeError(
                        f"{line['error']}"
                    )
                if line.get('id') is not None:
                    docker_id[line['id']] = line['status']
                live.update(get_lines(docker_id))
    except Exception as e:
        raise click.ClickException(
            f"An unexpected error occurred when pushing images: {e}"
        )


def prepare_publish_to_harbor(
        conf,
        version: str,
        public: bool,
        no_cache: bool = False
):
    username, secret = API.retrieve_harbor_creds(conf)
    registry = API.get_harbor_url(conf)
    if registry is None:
        raise click.UsageError("Something wrong when retrieving registry.")

    manifest = delta.manifest.parser.parse('manifest.json')
    with DeltaCore() as core:
        core.drive_build(
            version=version,
            registry=registry,
            no_cache=no_cache,
        )
    image_name = None
    project_name = f"{manifest.name}"
    if not project_name:
        raise click.UsageError(
            "Project name cannot be None or empty\n"
            "Set a name in your manifest"
        )

    docker_cli = docker.from_env()

    click.echo(f"Creating project {project_name}...")
    status = API.create_project_harbor(
        conf=conf,
        project_name=project_name,
        public=public
    )
    if status == 201:
        click.echo(f"Project {project_name} has been created")
    elif status == 409:
        click.echo(f"Project {project_name} already exists")
    else:
        raise click.UsageError(
            f"Something wrong when creating project {project_name}\n"
            f"status=({status})"
        )

    creds = {
        "username": username,
        "password": secret,
        "registry": registry
    }

    for name, _ in manifest.models.items():
        if name is None:
            raise click.UsageError("Model name cannot be None")
        image_name = f"{registry}/{project_name}/{name}"
        _push_image_to_registry(
            image_name=image_name,
            version=version,
            docker_cli=docker_cli,
            auth_config=creds
        )
        click.echo(f"{project_name}/{name} has been pushed.")
        docker_cli.images.remove(image=f"{image_name}:{version}", force=True)
    docker_cli.close()
