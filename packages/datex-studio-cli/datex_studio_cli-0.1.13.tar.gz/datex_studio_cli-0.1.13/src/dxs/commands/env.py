"""Environment commands: dxs env [list|components|deploy|list-authorized]."""

import click

from dxs.cli import DxsContext, pass_context
from dxs.core.api import (
    ApiClient,
    EnvironmentComponentsEndpoints,
    EnvironmentEndpoints,
)
from dxs.core.auth import require_auth, verify_org_match
from dxs.utils.errors import ValidationError
from dxs.utils.restricted import restrict_in_restricted_mode
from dxs.utils.responses import list_response, single


@click.group()
def env() -> None:
    """Environment commands.

    Manage and view environments and deployments in Datex Studio.

    \b
    Examples:
        dxs env list                    # List environments
        dxs env list --org 1            # List environments for organization
        dxs env components --env 1      # List components in environment
        dxs env deploy 100              # Deploy to environment component
        dxs env list-authorized         # List accessible components
    """
    pass


@env.command("list")
@click.option(
    "--org",
    "-o",
    type=int,
    default=None,
    help="Filter by organization ID",
)
@pass_context
@require_auth
def list_environments(ctx: DxsContext, org: int | None) -> None:
    """List environments.

    Returns a list of environments, optionally filtered by organization.

    \b
    Options:
        --org, -o  Filter by organization ID

    \b
    Examples:
        dxs env list
        dxs env list --org 1
    """
    client = ApiClient()

    # Resolve org_id from option or context (ctx.org is str, need to convert)
    org_id: int | None = org
    if org_id is None and ctx.org:
        org_id = int(ctx.org)

    if org_id:
        ctx.log(f"Fetching environments for organization {org_id}...")
    else:
        ctx.log("Fetching all environments...")

    environments = client.get(EnvironmentEndpoints.list(org_id))

    # Normalize to list
    if not isinstance(environments, list):
        environments = [environments] if environments else []

    ctx.output(
        list_response(
            items=environments,
            semantic_key="environments",
            organization_id=org_id,
        )
    )


@env.command("components")
@click.option(
    "--env",
    "-e",
    "env_id",
    type=int,
    default=None,
    help="Filter by environment ID",
)
@click.option(
    "--authorized",
    "-a",
    is_flag=True,
    default=False,
    help="Show only components the user is authorized to access",
)
@pass_context
@require_auth
def list_components(ctx: DxsContext, env_id: int | None, authorized: bool) -> None:
    """List environment components.

    Returns a list of environment components (deployed application instances).
    Use --env to filter by a specific environment, or --authorized to show
    only components you have access to.

    \b
    Options:
        --env, -e        Filter by environment ID
        --authorized, -a Show only authorized components

    \b
    Examples:
        dxs env components
        dxs env components --env 1
        dxs env components --authorized
    """
    client = ApiClient()

    if authorized:
        ctx.log("Fetching authorized environment components...")
        components = client.get(EnvironmentComponentsEndpoints.active_authorized())
    elif env_id:
        ctx.log(f"Fetching components for environment {env_id}...")
        components = client.get(EnvironmentComponentsEndpoints.list(env_id))
    else:
        ctx.log("Fetching all environment components...")
        components = client.get(EnvironmentComponentsEndpoints.list())

    # Normalize to list
    if not isinstance(components, list):
        components = [components] if components else []

    ctx.output(
        list_response(
            items=components,
            semantic_key="components",
            environment_id=env_id,
            authorized_only=authorized,
        )
    )


@env.command("deploy")
@click.argument("component_id", type=int)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Skip confirmation prompt",
)
@pass_context
@require_auth
@restrict_in_restricted_mode("deploys to environments")
def deploy(ctx: DxsContext, component_id: int, force: bool) -> None:
    """Deploy to an environment component.

    Triggers deployment of the latest version to the specified environment
    component.

    \b
    Arguments:
        COMPONENT_ID  Environment component ID to deploy to

    \b
    Options:
        --force, -f  Skip confirmation prompt

    \b
    Examples:
        dxs env deploy 100
        dxs env deploy 100 --force
    """
    client = ApiClient()

    # Get component info first
    ctx.log(f"Fetching environment component {component_id}...")
    component_info = client.get(EnvironmentComponentsEndpoints.get(component_id))

    component_name = component_info.get("name", f"Component {component_id}")
    environment_id = component_info.get("environmentId")
    is_active = component_info.get("isActive", False)

    # Check organization mismatch - deployment requires org membership
    if environment_id:
        ctx.log("Verifying organization access...")
        env_info = client.get(EnvironmentEndpoints.get(environment_id))
        org_id = env_info.get("organizationId")
        org_name = env_info.get("organization", {}).get("name") if env_info.get("organization") else None
        if org_id:
            verify_org_match(org_id, org_name)

    if not is_active:
        raise ValidationError(
            message=f"Environment component {component_id} is not active",
            suggestions=[
                "Verify the component ID is correct",
                "Use 'dxs env components' to see active components",
            ],
        )

    if not force:
        if not click.confirm(
            f"Deploy to environment component '{component_name}' (ID: {component_id})?"
        ):
            ctx.output(
                single(
                    item={"deployed": False, "reason": "User cancelled"},
                    semantic_key="deploy_result",
                    component_id=component_id,
                )
            )
            return

    ctx.log(f"Deploying to '{component_name}'...")
    result = client.post(EnvironmentComponentsEndpoints.deploy(component_id))

    ctx.output(
        single(
            item={
                "deployed": True,
                "component_id": component_id,
                "component_name": component_name,
                "environment_id": environment_id,
                "result": result,
            },
            semantic_key="deploy_result",
        )
    )


@env.command("list-authorized")
@pass_context
@require_auth
def list_authorized(ctx: DxsContext) -> None:
    """List active environment components the user is authorized to access.

    Returns a list of environment components that are active and that the
    current user has permission to access.

    \b
    Example:
        dxs env list-authorized
    """
    client = ApiClient()
    ctx.log("Fetching authorized environment components...")

    environments = client.get(EnvironmentComponentsEndpoints.active_authorized())

    # Normalize to list
    if not isinstance(environments, list):
        environments = [environments] if environments else []

    ctx.output(
        list_response(
            items=environments,
            semantic_key="environments",
        )
    )
