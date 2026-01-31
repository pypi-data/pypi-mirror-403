"""Explore commands: dxs source explore [configs|config|summary|trace|info|graph]."""

import re
import threading
from pathlib import Path
from typing import Any, cast

import click
import yaml

from dxs.cli import DxsContext, pass_context
from dxs.core.api import ApiClient, BranchEndpoints, ConfigurationEndpoints, DependencyEndpoints
from dxs.core.api.models import ConfigurationOutput
from dxs.core.auth import require_auth
from dxs.core.cache import end_cache_session, get_cache, start_cache_session
from dxs.core.output.yaml_fmt import convert_code_to_literal
from dxs.utils.errors import ApiError, ValidationError
from dxs.utils.restricted import check_restricted_mode_for_option, restrict_in_restricted_mode
from dxs.utils.responses import list_response, single

# Module-level cache for config index: branch_id -> {ref_name_lower: (type, id, app_ref_name, is_external)}
_config_index_cache: dict[int, dict[str, tuple[str, int, str, bool]]] = {}
_config_index_lock = threading.Lock()

# Cache for branch info
_branch_info_cache: dict[int, dict[str, Any]] = {}
_branch_info_lock = threading.Lock()

# Dialog-triggering node kinds in flows
DIALOG_KINDS = {"displayModal", "showDialog", "openFlyout", "displayFlyout", "openModal"}

# Dialog-related config keys where component references may be found
DIALOG_KEYS = {"modalConfig", "dialogConfig", "flyoutConfig", "contentConfig", "panelConfig"}

# Regex pattern to detect dialogs opened via TypeScript $shell calls
# Matches patterns like: $shell.ModuleName.opencomponent_name() or $shell.ModuleName.opencomponent_nameDialog()
SHELL_OPEN_PATTERN = re.compile(r"\$shell\.(\w+)\.open(\w+?)(?:Dialog)?\s*\(")

# Regex pattern to detect backend flow invocations via TypeScript $flows calls
# Matches patterns like: $flows.ModuleName.flow_name() or await $flows.ModuleName.flow_name({})
FLOWS_CALL_PATTERN = re.compile(r"\$flows\.(\w+)\.(\w+)\s*\(")

# Regex pattern to detect frontend flow invocations via TypeScript $frontendFlows calls
# Matches patterns like: $frontendFlows.Module.flow_name() or await $frontendFlows.Module.flow_name({})
FRONTEND_FLOWS_CALL_PATTERN = re.compile(r"\$frontendFlows\.(\w+)\.(\w+)\s*\(")

# Regex pattern to detect datasource invocations via TypeScript $datasources calls
# Matches patterns like: $datasources.ModuleName.datasource_name.get({}) or .execute({})
DATASOURCES_CALL_PATTERN = re.compile(r"\$datasources\.(\w+)\.(\w+)\.(?:get|execute|getList)\s*\(")

# Regex pattern to detect API invocations via TypeScript $apis calls
# Matches patterns like: $apis.Module.ApiName.Controller.Method({}) or $apis.Module.ApiName.Method({})
# The pattern captures the full chain after $apis. and extracts the last method name
APIS_CALL_PATTERN = re.compile(r"\$apis\.(\w+(?:\.\w+)+)\s*\(")

# Regex pattern to detect security policy/operation checks via TypeScript $operations calls
# Matches patterns like: $operations.Module.operation_name.isAssignedToAll()
OPERATIONS_CALL_PATTERN = re.compile(r"\$operations\.(\w+)\.(\w+)\.isAssigned")

# Regex pattern to detect custom type references via TypeScript $types
# Matches patterns like: $types.Module.type_name or $types.Module.e_enum_name
TYPES_REF_PATTERN = re.compile(r"\$types\.(\w+)\.(\w+)")

# Regex pattern to detect direct API calls via $api (platform APIs)
# Matches patterns like: $api.GetCurrentUserInfo({}) or $api.ReserveEntityIdBatch({})
DIRECT_API_PATTERN = re.compile(r"\$api\.(\w+)\s*\(")

# Regex pattern to detect private flow calls via $hub, $form, $grid, etc.
# Matches patterns like: $hub.apply_operations() or $form.on_submit()
# These are flows defined inline within the config itself
PRIVATE_FLOW_CALL_PATTERN = re.compile(r"\$(hub|form|grid|editor|wizard|shell)\.(\w+)\s*\(")

# Regex pattern to detect settings references via TypeScript $settings
# Matches patterns like: $settings.FootprintManager.ExcelExportLimit
SETTINGS_REF_PATTERN = re.compile(r"\$settings\.(\w+)\.(\w+)")

# Regex pattern to detect database table references via TypeScript $db calls
# Matches patterns like: $db.Module.table_name.where() or .update() or .remove() or .insert()
DB_CALL_PATTERN = re.compile(r"\$db\.(\w+)\.(\w+)\.(?:where|update|remove|first|insert|all)\s*\(")

# Regex pattern to detect job scheduling via TypeScript $services calls
# Matches patterns like: $services.jobs.Module.flow_name.schedule.create()
SERVICES_JOBS_PATTERN = re.compile(r"\$services\.jobs\.(\w+)\.(\w+)\.schedule")

# Regex pattern to detect dynamic flow references via bracket notation
# Matches patterns like: $flows[variableName].method() - cannot be statically resolved
DYNAMIC_FLOWS_PATTERN = re.compile(r"\$flows\[\w+\]")

# All 28 configuration types supported by Datex Studio
CONFIGURATION_TYPES = [
    "grid",
    "hub",
    "form",
    "editor",
    "shell",
    "calendar",
    "list",
    "widget",
    "selector",
    "datasource",
    "flow",
    "frontendflow",
    "wizard",
    "card",
    "report",
    "embed",
    "codeeditor",
    "visualization",
    "localization",
    "storage",
    "customtype",
    "endpoint",
    "securitypolicy",
    "footprintflow",
    "footprintdatasource",
    "footprintworkflow",
    "backendtest",
]


def _resolve_branch_id(ctx: DxsContext, branch: int | None) -> int:
    """Resolve branch ID from option or context."""
    if branch:
        return branch

    if ctx.branch:
        return ctx.branch

    raise ValidationError(
        message="Branch ID required",
        suggestions=[
            "Use --branch flag: dxs source explore configs --branch 100",
            "Set environment variable: export DXS_BRANCH=100",
        ],
    )


def _get_branch_info(client: ApiClient, branch_id: int) -> dict[str, Any]:
    """Get and cache branch information.

    Uses two-tier caching:
    1. In-memory cache (fast, within single invocation)
    2. SQLite cache (persistent, for immutable branches only)
    """
    # Check in-memory cache first (with lock for thread safety)
    with _branch_info_lock:
        if branch_id in _branch_info_cache:
            return _branch_info_cache[branch_id]

    # Check SQLite cache
    cache = get_cache()
    cached = cache.get_branch_info(branch_id)
    if cached is not None:
        with _branch_info_lock:
            _branch_info_cache[branch_id] = cached
        return cached

    # Fetch from API
    try:
        branch_data: dict[str, Any] = client.get(BranchEndpoints.get(branch_id))
        with _branch_info_lock:
            _branch_info_cache[branch_id] = branch_data

        # Persist to SQLite if cacheable (immutable branch)
        status = branch_data.get("applicationStatusId", 0)
        cache.set_branch_info(branch_id, status, branch_data)

        return branch_data
    except Exception:
        return {}


def _get_branch_app_name(client: ApiClient, branch_id: int) -> str:
    """Get the application name for a branch.

    Tries in order:
    1. Branch's referenceName field
    2. applicationDefinition.name field

    Returns empty string if neither is found.
    """
    branch_info = _get_branch_info(client, branch_id)

    # First try referenceName
    ref_name = branch_info.get("referenceName")
    if ref_name:
        return str(ref_name)

    # Fall back to applicationDefinition.name
    app_def = branch_info.get("applicationDefinition", {})
    if isinstance(app_def, dict):
        app_name = app_def.get("name")
        if app_name:
            return str(app_name)

    return ""


def _is_config_owned(cfg: dict[str, Any]) -> bool:
    """Check if a configuration is owned by the current branch.

    Configs with isExternal=False are owned by the branch.
    Configs with isExternal=True are referenced from libraries.
    """
    return not cfg.get("isExternal", False)


def _normalize_config_type(config_type: str) -> str:
    """Normalize configuration type to lowercase."""
    return config_type.lower().strip()


def _extract_config_summary(config: dict[str, Any], config_type: str) -> dict[str, Any]:
    """Extract summary fields from a configuration."""
    return {
        "id": config.get("id"),
        "referenceName": config.get("referenceName"),
        "label": config.get("label"),
        "description": config.get("description"),
        "accessModifier": config.get("accessModifier"),
        "configType": config_type,
        "applicationReferenceName": config.get("applicationReferenceName"),
        "isExternal": config.get("isExternal", False),
    }


def _get_json_content(config: dict[str, Any]) -> dict[str, Any]:
    """Extract JSON content from config.

    Handles multiple formats:
    - API mode: config has 'json' or 'config' wrapper field
    - Filesystem mode: config IS the content (no wrapper)
    """
    # Try API-style wrappers first
    wrapped = config.get("json") or config.get("config")
    if wrapped:
        return cast(dict[str, Any], wrapped)
    # Filesystem mode: config is already the content
    # Return as-is if it has typical config fields
    if any(k in config for k in ("toolbar", "columns", "tabs", "menubar", "nodes")):
        return config
    return config


def _build_config_index(
    client: ApiClient, branch_id: int, ctx: DxsContext
) -> dict[str, tuple[str, int, str, bool]]:
    """Build reference_name -> (type, id, app_ref_name, is_external) index for a branch.

    Uses two-tier caching:
    1. In-memory cache (fast, within single invocation)
    2. SQLite cache (persistent, for immutable branches only)
    """
    # Check in-memory cache first (with lock for thread safety)
    with _config_index_lock:
        if branch_id in _config_index_cache:
            return _config_index_cache[branch_id]

    # Check SQLite cache
    cache = get_cache()
    cached = cache.get_config_index(branch_id)
    if cached is not None:
        ctx.log(f"Using cached configuration index for branch {branch_id} ({len(cached)} configs)")
        with _config_index_lock:
            _config_index_cache[branch_id] = cached
        return cached

    # Build fresh from API
    ctx.log(f"Building configuration index for branch {branch_id}...")
    index: dict[str, tuple[str, int, str, bool]] = {}

    for ctype in CONFIGURATION_TYPES:
        try:
            configs = client.get(ConfigurationEndpoints.list_all(branch_id, ctype))
            if not isinstance(configs, list):
                configs = [configs] if configs else []
            for cfg in configs:
                ref_name = cfg.get("referenceName", "")
                app_ref = cfg.get("applicationReferenceName", "")
                is_external = cfg.get("isExternal", False)
                if ref_name:
                    key = ref_name.lower()
                    # Prefer owned configs over external ones when there are duplicates
                    existing = index.get(key)
                    if existing is None:
                        index[key] = (ctype, cfg.get("id"), app_ref, is_external)
                    elif not is_external and existing[3]:
                        # New config is owned, existing is external - replace
                        index[key] = (ctype, cfg.get("id"), app_ref, is_external)
        except ApiError as e:
            # Log JSON parse errors as warnings (e.g., endpoints type)
            if e.code == "DXS-API-JSON-001":
                ctx.log(f"Warning: {ctype} returned non-JSON response")
            # Other API errors are expected (type may not exist)
        except Exception:
            pass

    with _config_index_lock:
        _config_index_cache[branch_id] = index
    ctx.log(f"Indexed {len(index)} configurations")

    # Persist to SQLite if cacheable (immutable branch)
    branch_info = _get_branch_info(client, branch_id)
    branch_status = branch_info.get("applicationStatusId", 0)
    cache.set_config_index(branch_id, branch_status, index)

    return index


def _lookup_config(
    client: ApiClient, branch_id: int, reference_name: str, ctx: DxsContext
) -> tuple[str, int, str, bool] | None:
    """Fast lookup of config type, ID, app ref name, and is_external by reference name."""
    index = _build_config_index(client, branch_id, ctx)
    return index.get(reference_name.lower())


def _get_config_content_cached(
    client: ApiClient,
    branch_id: int,
    config_type: str,
    config_id: int,
    branch_status: int,
) -> dict[str, Any] | None:
    """Fetch config content with caching support.

    Uses SQLite cache for immutable branches to avoid redundant API calls.
    """
    cache = get_cache()

    # Check cache
    cached = cache.get_config_content(branch_id, config_type, config_id)
    if cached is not None:
        return cached

    # Fetch from API
    try:
        content: dict[str, Any] = client.get(
            ConfigurationEndpoints.get_content(branch_id, config_type, config_id)
        )

        # Cache if branch is cacheable (immutable)
        ref_name = content.get("referenceName", "")
        cache.set_config_content(
            branch_id, branch_status, config_type, config_id, ref_name, content
        )

        return content
    except Exception:
        return None


def _get_references_cached(
    config: dict[str, Any],
    config_type: str,
    config_id: int,
    branch_id: int,
    branch_status: int,
    config_index: dict[str, tuple[str, int, str, bool]],
) -> dict[str, list[str]]:
    """Get extracted references with caching support.

    Uses SQLite cache for immutable branches to avoid redundant parsing.
    """
    cache = get_cache()

    # Check cache
    cached = cache.get_references(branch_id, config_type, config_id)
    if cached is not None:
        return cached

    # Extract fresh
    references = _extract_all_references(config, config_type, config_index)

    # Cache if branch is cacheable (immutable)
    cache.set_references(branch_id, branch_status, config_type, config_id, references)

    return references


def _extract_toolbar_actions(toolbar: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Extract toolbar button info from toolbar config."""
    if not toolbar:
        return []
    actions = []
    for item in toolbar:
        if item.get("type") == "button":
            btn_cfg = item.get("buttonConfig") or {}
            click_cfg = btn_cfg.get("clickFlowConfig") or {}
            actions.append(
                {
                    "id": item.get("id"),
                    "label": btn_cfg.get("label"),
                    "flow": click_cfg.get("flowId"),
                }
            )
    return actions


def _extract_flow_calls(json_content: dict[str, Any]) -> list[str]:
    """Recursively extract flow references from flow config."""
    flows: set[str] = set()

    def _scan(obj: Any) -> None:
        if isinstance(obj, dict):
            if obj.get("kind") == "invokeFlow" or obj.get("type") == "invokeFlow":
                flow_name = obj.get("flow") or obj.get("referenceName")
                if flow_name:
                    flows.add(flow_name)
            for key in ["onClick", "onSubmit", "onCancel", "onSave", "flow"]:
                if key in obj and isinstance(obj[key], str):
                    flows.add(obj[key])
            for v in obj.values():
                _scan(v)
        elif isinstance(obj, list):
            for item in obj:
                _scan(item)

    _scan(json_content)
    return sorted(flows)


def _extract_datasource_refs(json_content: dict[str, Any]) -> list[str]:
    """Recursively extract datasource references from config."""
    datasources: set[str] = set()

    def _scan(obj: Any) -> None:
        if isinstance(obj, dict):
            for key in ["datasource", "ds", "datasourceConfig"]:
                val = obj.get(key)
                if isinstance(val, str) and val:
                    datasources.add(val)
                elif isinstance(val, dict):
                    # datasourceConfig may have configId
                    ds_id = val.get("configId") or val.get("datasource")
                    if ds_id:
                        datasources.add(ds_id)
            if obj.get("kind") == "invokeDatasource" or obj.get("type") == "invokeDatasource":
                ds_name = obj.get("datasource") or obj.get("referenceName")
                if ds_name:
                    datasources.add(ds_name)
            for v in obj.values():
                _scan(v)
        elif isinstance(obj, list):
            for item in obj:
                _scan(item)

    _scan(json_content)
    return sorted(datasources)


def _extract_grid_datasource(json_content: dict[str, Any]) -> str | None:
    """Extract the primary datasource from a grid config."""
    # Try direct datasource field
    ds = json_content.get("datasource")
    if isinstance(ds, str):
        return ds

    # Try datasourceConfig
    ds_config = json_content.get("datasourceConfig")
    if isinstance(ds_config, dict):
        config_id = ds_config.get("configId")
        if isinstance(config_id, str):
            return config_id
        ds_val = ds_config.get("datasource")
        if isinstance(ds_val, str):
            return ds_val
        return None
    elif isinstance(ds_config, str):
        return ds_config

    # Try dataConfig.datasource
    data_config = json_content.get("dataConfig")
    if isinstance(data_config, dict):
        ds_val = data_config.get("datasource")
        if isinstance(ds_val, str):
            return ds_val
        config_id = data_config.get("configId")
        if isinstance(config_id, str):
            return config_id

    return None


def _extract_type_summary(config: dict[str, Any], config_type: str) -> dict[str, Any]:
    """Extract type-specific structural summary from a configuration."""
    json_content = _get_json_content(config)

    # Handle null/empty content
    if json_content is None:
        return {"error": "Configuration has no content"}

    if config_type == "grid":
        # Columns can have 'id' or 'field' depending on config version
        columns = []
        for c in json_content.get("columns", []):
            col_id = c.get("id") or c.get("field")
            col_header = c.get("header") or c.get("headerName") or c.get("id")
            columns.append({"field": col_id, "header": col_header})
        return {
            "datasource": _extract_grid_datasource(json_content),
            "columns": columns,
            "toolbar_buttons": _extract_toolbar_actions(json_content.get("topToolbar")),
            "row_actions": _extract_toolbar_actions(json_content.get("rowActions")),
        }
    elif config_type == "form":
        return {
            "fields": [
                {"id": f.get("id"), "control": f.get("control"), "label": f.get("label")}
                for f in json_content.get("fields", [])
            ],
            "submit_flow": json_content.get("onSubmit"),
            "cancel_flow": json_content.get("onCancel"),
        }
    elif config_type == "editor":
        sections = []
        for s in json_content.get("sections", []):
            sections.append(
                {
                    "id": s.get("id"),
                    "title": s.get("title"),
                    "fields": [f.get("id") for f in s.get("fields", [])],
                }
            )
        return {
            "datasource": json_content.get("datasource"),
            "sections": sections,
            "save_flow": json_content.get("onSave"),
        }
    elif config_type in ("flow", "frontendflow", "footprintflow"):
        in_params = json_content.get("inParams") or []
        out_params = json_content.get("outParams") or []
        return {
            "inParams": [p.get("id") for p in in_params if isinstance(p, dict)],
            "outParams": [p.get("id") for p in out_params if isinstance(p, dict)],
            "called_flows": _extract_flow_calls(json_content),
            "called_datasources": _extract_datasource_refs(json_content),
        }
    elif config_type in ("datasource", "footprintdatasource"):
        return {
            "endpoint": json_content.get("endpoint"),
            "query": json_content.get("query"),
            "return_fields": [
                f.get("id") for f in json_content.get("returnParams", []) if isinstance(f, dict)
            ],
        }
    elif config_type == "selector":
        return {
            "datasource": json_content.get("datasource"),
            "value_field": json_content.get("valueField"),
            "display_field": json_content.get("displayField"),
        }
    elif config_type == "hub":
        tabs = []
        for t in json_content.get("tabs") or []:
            content_config = t.get("contentConfig") or {}
            tabs.append(
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "contentType": t.get("contentType"),
                    "configId": content_config.get("configId"),
                }
            )
        return {
            "tabs": tabs,
            "toolbar": _extract_toolbar_actions(json_content.get("toolbar")),
        }
    elif config_type == "shell":
        menubar = [
            {
                "id": m.get("id"),
                "label": m.get("label"),
                "items": [i.get("label") for i in m.get("items", []) if isinstance(i, dict)],
            }
            for m in json_content.get("menubar", [])
        ]
        return {
            "home": json_content.get("home"),
            "menubar": menubar,
            "toolbar": _extract_toolbar_actions(json_content.get("toolbar")),
        }
    elif config_type in ("customtype", "storage"):
        fields = []
        obj_type_def = json_content.get("objectTypeDef", [])
        if isinstance(obj_type_def, list):
            for item in obj_type_def:
                if isinstance(item, dict):
                    # Check for nested objectTypeDef (wrapper pattern)
                    nested_def = item.get("objectTypeDef")
                    if nested_def and isinstance(nested_def, list):
                        for field in nested_def:
                            if isinstance(field, dict):
                                fields.append(
                                    {
                                        "id": field.get("id"),
                                        "type": field.get("type"),
                                        "required": field.get("required"),
                                        "isCollection": field.get("isCollection", False),
                                    }
                                )
                    else:
                        # Direct field definition
                        fields.append(
                            {
                                "id": item.get("id"),
                                "type": item.get("type"),
                                "required": item.get("required"),
                                "isCollection": item.get("isCollection", False),
                            }
                        )
        result: dict[str, Any] = {"fields": fields}
        if json_content.get("type"):
            result["interface_type"] = json_content.get("type")
        if json_content.get("baseTypes"):
            result["baseTypes"] = json_content.get("baseTypes")
        if json_content.get("enumTypeDef"):
            result["enumValues"] = [
                e.get("id") for e in json_content.get("enumTypeDef", []) if isinstance(e, dict)
            ]
        return result
    else:
        return {"keys": list(json_content.keys()) if json_content else []}


def _generate_context_data(
    config: dict[str, Any],
    config_type: str,
    ref_name: str,
    source_file: str,
    library: str | None,
    config_index: dict[str, tuple[str, int, str, bool]],
    library_branches: dict[str, int],
    main_branch_id: int,
) -> dict[str, Any]:
    """Generate combined context data with structure and references.

    Combines the structural information from _extract_type_summary() with
    dependency references from _extract_all_references(), providing a single
    comprehensive context file for each config.

    Args:
        config: The raw config dict (usually from raw_config key)
        config_type: Type of config (flow, grid, datasource, etc.)
        ref_name: Reference name of the config
        source_file: Relative path to the source file
        library: Library name or None if local
        config_index: Index for looking up config types
        library_branches: Mapping of library names to branch IDs
        main_branch_id: The main (local) branch ID

    Returns:
        Combined context dict ready to be written to .context.yaml
    """
    from datetime import datetime, timezone

    # Extract basic metadata
    context_data: dict[str, Any] = {
        "reference_name": ref_name,
        "config_type": config_type,
        "label": config.get("label") or config.get("title"),
        "description": config.get("description"),
        "library": library,
        "source_file": source_file,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Extract type-specific structural info
    # Use _extract_type_summary but filter out dependency fields that will be in references
    type_summary = _extract_type_summary(config, config_type)

    # Remove fields that are now in references (they were sparse/empty anyway)
    dependency_fields = {"called_flows", "called_datasources"}
    structure = {k: v for k, v in type_summary.items() if k not in dependency_fields}

    if structure:
        context_data["structure"] = structure

    # Extract and enrich references
    basic_refs = _extract_all_references(config, config_type, config_index)
    references = _enrich_with_library(basic_refs, config_index, library_branches, main_branch_id)

    if references:
        context_data["references"] = references

    return context_data


def _add_to_refs_by_type(
    refs: dict[str, set[str]],
    config_id: str,
    config_index: dict[str, tuple[str, int, str, bool]],
    explicit_type: str = "",
) -> None:
    """Add component to refs dict, using explicit type or index lookup."""
    type_lower = explicit_type.lower() if explicit_type else ""

    # Priority 1: Use explicit type if valid
    if type_lower in CONFIGURATION_TYPES:
        refs.setdefault(type_lower + "s", set()).add(config_id)
        return

    # Priority 2: Look up in index
    lookup = config_index.get(config_id.lower())
    if lookup:
        actual_type = lookup[0]  # (type, id, app_ref, is_external)
        refs.setdefault(actual_type + "s", set()).add(config_id)
    else:
        # Not in index - add to generic "components" category
        refs.setdefault("components", set()).add(config_id)


def _extract_all_references(
    config: dict[str, Any],
    config_type: str,
    config_index: dict[str, tuple[str, int, str, bool]],
) -> dict[str, list[str]]:
    """Extract all configuration references from a config."""
    json_content = _get_json_content(config)
    refs: dict[str, set[str]] = {
        "datasources": set(),
        "private_frontend_flows": set(),
        "forms": set(),
        "editors": set(),
        "selectors": set(),
        "grids": set(),
        "hubs": set(),
        "dialogs": set(),
        "widgets": set(),
    }

    def _scan(obj: Any) -> None:
        if isinstance(obj, dict):
            # API setting references (used by datasources)
            if "apiSettingName" in obj and isinstance(obj["apiSettingName"], str):
                refs.setdefault("api_settings", set()).add(obj["apiSettingName"])

            # Linked datasources (datasource-to-datasource references)
            if "linkedDatasources" in obj and isinstance(obj["linkedDatasources"], list):
                for linked in obj["linkedDatasources"]:
                    if isinstance(linked, dict):
                        ds_config = linked.get("datasourceConfig")
                        if isinstance(ds_config, dict):
                            config_id = ds_config.get("configId")
                            if config_id and isinstance(config_id, str):
                                refs["datasources"].add(config_id)

            # Datasource references
            for key in ["datasource", "ds"]:
                if key in obj and isinstance(obj[key], str):
                    refs["datasources"].add(obj[key])

            # Flow references - direct keys (frontend flows defined in config)
            for key in [
                "onClick",
                "onSubmit",
                "onCancel",
                "onSave",
                "flow",
                "onRowDoubleClick",
                "flowId",
            ]:
                if key in obj and isinstance(obj[key], str):
                    refs["private_frontend_flows"].add(obj[key])

            # Flow references - nested clickFlowConfig and other flow config variants
            for flow_config_key in [
                "clickFlowConfig",
                "uiValueChangeFlowConfig",
                "selectionChangeFlowConfig",
                "validationFlowConfig",
                "visibilityFlowConfig",
                "enabledFlowConfig",
                "onChangeFlowConfig",
                "loadFlowConfig",
            ]:
                if flow_config_key in obj and isinstance(obj[flow_config_key], dict):
                    flow_id = obj[flow_config_key].get("flowId")
                    if flow_id:
                        refs["private_frontend_flows"].add(flow_id)

            # Flow invocation nodes
            if obj.get("kind") == "invokeFlow":
                if fn := obj.get("flow") or obj.get("referenceName"):
                    refs["private_frontend_flows"].add(fn)
            if obj.get("kind") == "invokeDatasource":
                if dn := obj.get("datasource") or obj.get("referenceName"):
                    refs["datasources"].add(dn)

            # Declarative operation references (operationId in buttons/toolbar for permissions)
            if "operationId" in obj and isinstance(obj["operationId"], str):
                refs.setdefault("operations", set()).add(obj["operationId"])

            # Dialog-triggering flow nodes (displayModal, openFlyout, etc.)
            node_kind = obj.get("kind") or obj.get("type")
            if node_kind in DIALOG_KINDS:
                # Extract component being displayed as dialog
                for dialog_key in DIALOG_KEYS:
                    dialog_cfg = obj.get(dialog_key)
                    if isinstance(dialog_cfg, dict):
                        config_id = dialog_cfg.get("configId")
                        if config_id and isinstance(config_id, str):
                            refs["dialogs"].add(config_id)
                            _add_to_refs_by_type(refs, config_id, config_index)

            # Component references
            for key in ["component", "editor", "form", "grid", "hub"]:
                if key in obj and isinstance(obj[key], str):
                    _add_to_refs_by_type(refs, obj[key], config_index)

            if "selector" in obj and isinstance(obj["selector"], str):
                refs["selectors"].add(obj["selector"])

            # Widget references
            if "widget" in obj and isinstance(obj["widget"], str):
                refs["widgets"].add(obj["widget"])
            # Widget config references (widgetConfig.configId pattern)
            if "widgetConfig" in obj and isinstance(obj["widgetConfig"], dict):
                widget_id = obj["widgetConfig"].get("configId")
                if widget_id and isinstance(widget_id, str):
                    refs["widgets"].add(widget_id)

            # Hub tab content references (contentConfig.configId)
            if "contentConfig" in obj and isinstance(obj["contentConfig"], dict):
                config_id = obj["contentConfig"].get("configId")
                content_type = obj.get("contentType", "")
                if config_id and isinstance(config_id, str):
                    _add_to_refs_by_type(refs, config_id, config_index, content_type)

            # Shell menu/home view references (viewConfig.configId)
            if "viewConfig" in obj and isinstance(obj["viewConfig"], dict):
                config_id = obj["viewConfig"].get("configId")
                view_type = obj.get("viewType", "")
                if config_id and isinstance(config_id, str):
                    _add_to_refs_by_type(refs, config_id, config_index, view_type)

            # Dropdown/selector references (dropdownConfig.configId in selectBox controls)
            if "dropdownConfig" in obj and isinstance(obj["dropdownConfig"], dict):
                config_id = obj["dropdownConfig"].get("configId")
                if config_id and isinstance(config_id, str):
                    refs["selectors"].add(config_id)

            # Additional selector config patterns (autocomplete, lookup, selectBox controls)
            for selector_config_key in [
                "autocompleteConfig",
                "lookupConfig",
                "selectBoxConfig",
                "selectorConfig",
            ]:
                if selector_config_key in obj and isinstance(obj[selector_config_key], dict):
                    # Check for configId or selectorConfigId
                    config_id = obj[selector_config_key].get("configId") or obj[
                        selector_config_key
                    ].get("selectorConfigId")
                    if config_id and isinstance(config_id, str):
                        refs["selectors"].add(config_id)

            # Datasource config references (datasourceConfig.configId in selectors, widgets, calendars, etc.)
            if "datasourceConfig" in obj and isinstance(obj["datasourceConfig"], dict):
                config_id = obj["datasourceConfig"].get("configId")
                if config_id and isinstance(config_id, str):
                    refs["datasources"].add(config_id)

            # Event content config references (eventContentConfig.configId in calendars for card references)
            if "eventContentConfig" in obj and isinstance(obj["eventContentConfig"], dict):
                config_id = obj["eventContentConfig"].get("configId")
                if config_id and isinstance(config_id, str):
                    refs.setdefault("cards", set()).add(config_id)

            # Custom type references (objectType in customtype configs, e.g., "Module.TypeName")
            if "objectType" in obj and isinstance(obj["objectType"], str):
                object_type = obj["objectType"]
                # Extract just the type name (after the last dot)
                if "." in object_type:
                    type_name = object_type.rsplit(".", 1)[-1]
                    refs.setdefault("types", set()).add(type_name)

            # Base type references in custom types (baseTypes array, e.g., ["Module.BaseType"])
            if "baseTypes" in obj and isinstance(obj["baseTypes"], list):
                for base_type in obj["baseTypes"]:
                    if isinstance(base_type, str) and "." in base_type:
                        type_name = base_type.rsplit(".", 1)[-1]
                        refs.setdefault("types", set()).add(type_name)

            # Detect references from TypeScript code in executeCodeConfig.code
            if "executeCodeConfig" in obj and isinstance(obj["executeCodeConfig"], dict):
                code = obj["executeCodeConfig"].get("code")
                if code and isinstance(code, str):
                    # Find all $shell.Module.openComponent() patterns (dialogs)
                    for match in SHELL_OPEN_PATTERN.finditer(code):
                        module_name = match.group(1)
                        component_name = match.group(2)
                        # Store with module prefix for accurate library attribution
                        refs["dialogs"].add(f"{module_name}::{component_name}")
                    # Find all $flows.Module.flow_name() patterns (backend flow invocations)
                    for match in FLOWS_CALL_PATTERN.finditer(code):
                        module_name = match.group(1)
                        flow_name = match.group(2)
                        # Store with module prefix for accurate library attribution
                        refs.setdefault("backend_flows", set()).add(f"{module_name}::{flow_name}")
                    # Find all $frontendFlows.Module.flow_name() patterns (frontend flow invocations)
                    for match in FRONTEND_FLOWS_CALL_PATTERN.finditer(code):
                        module_name = match.group(1)
                        flow_name = match.group(2)
                        refs.setdefault("frontend_flows", set()).add(f"{module_name}::{flow_name}")
                    # Find all $datasources.Module.datasource_name.get/execute() patterns
                    for match in DATASOURCES_CALL_PATTERN.finditer(code):
                        module_name = match.group(1)
                        datasource_name = match.group(2)
                        refs["datasources"].add(f"{module_name}::{datasource_name}")
                    # Find all $apis.Module.ApiName.Method() patterns (API invocations)
                    for match in APIS_CALL_PATTERN.finditer(code):
                        # Full chain like "SalesOrders.FootprintApi.Shipments.CompleteSalesOrderShipment"
                        full_chain = match.group(1)

                        # Check for FootprintApi special patterns
                        if ".FootprintApi.extendedActions." in full_chain:
                            # Extract flow name: part after "extendedActions."
                            # e.g., "SalesOrders.FootprintApi.extendedActions.create_order" -> "create_order"
                            parts = full_chain.split(".FootprintApi.extendedActions.")
                            if len(parts) > 1:
                                flow_name = parts[1].split(".")[0]
                                refs.setdefault("footprintflows", set()).add(flow_name)
                        elif ".FootprintApi.datasources." in full_chain:
                            # Extract datasource name: part after "datasources." but before ".get/.execute/.getList"
                            # e.g., "Module.FootprintApi.datasources.fpds_find_orders.get" -> "fpds_find_orders"
                            parts = full_chain.split(".FootprintApi.datasources.")
                            if len(parts) > 1:
                                ds_name = parts[1].split(".")[0]
                                refs.setdefault("footprintdatasources", set()).add(ds_name)
                        else:
                            # Regular API call - last part is the method name
                            api_method = full_chain.rsplit(".", 1)[-1]
                            refs.setdefault("apis", set()).add(api_method)
                    # Find all $operations.Module.operation_name.isAssigned() patterns
                    for match in OPERATIONS_CALL_PATTERN.finditer(code):
                        module_name = match.group(1)
                        operation_name = match.group(2)
                        refs.setdefault("operations", set()).add(f"{module_name}::{operation_name}")
                    # Find all $types.Module.type_name patterns
                    for match in TYPES_REF_PATTERN.finditer(code):
                        module_name = match.group(1)
                        type_name = match.group(2)
                        refs.setdefault("types", set()).add(f"{module_name}::{type_name}")
                    # Find all $api.MethodName() patterns (direct platform API calls)
                    for match in DIRECT_API_PATTERN.finditer(code):
                        api_method = match.group(1)
                        refs.setdefault("platform_apis", set()).add(api_method)
                    # Find all $hub.flow_name(), $form.flow_name(), etc. (private flows)
                    for match in PRIVATE_FLOW_CALL_PATTERN.finditer(code):
                        flow_name = match.group(2)
                        # Skip built-in properties/methods that aren't flows
                        if flow_name not in ("vars", "tabs", "fields", "toolbar", "refresh"):
                            refs["private_frontend_flows"].add(flow_name)
                    # Find all $settings.Module.SettingName patterns
                    for match in SETTINGS_REF_PATTERN.finditer(code):
                        module_name = match.group(1)
                        setting_name = match.group(2)
                        refs.setdefault("settings", set()).add(f"{module_name}::{setting_name}")
                    # Find all $db.Module.table_name.method() patterns (database table references)
                    for match in DB_CALL_PATTERN.finditer(code):
                        module_name = match.group(1)
                        table_name = match.group(2)
                        refs.setdefault("database_tables", set()).add(f"{module_name}.{table_name}")
                    # Find all $services.jobs.Module.flow_name.schedule patterns (scheduled jobs)
                    for match in SERVICES_JOBS_PATTERN.finditer(code):
                        flow_name = match.group(2)
                        refs.setdefault("scheduled_jobs", set()).add(flow_name)
                    # Detect if dynamic flow references exist (can't be statically resolved)
                    if DYNAMIC_FLOWS_PATTERN.search(code):
                        refs.setdefault("_dynamic_references", set()).add("flows")

            for v in obj.values():
                _scan(v)
        elif isinstance(obj, list):
            for item in obj:
                _scan(item)

    _scan(json_content)
    return {k: sorted(v) for k, v in refs.items() if v}


def _enrich_references(
    basic_refs: dict[str, list[str]],
    config_index: dict[str, tuple[str, int, str, bool]],
    library_branches: dict[str, int],
    main_branch_id: int,
) -> dict[str, list[dict[str, Any]]]:
    """Convert reference names to structured objects with library info.

    Args:
        basic_refs: Reference names grouped by type (from _extract_all_references)
        config_index: Lookup dict: ref_name_lower -> (type, id, app_ref, is_external)
        library_branches: Library name -> branch_id mapping
        main_branch_id: Branch ID of the main application

    Returns:
        Dict with same keys but values are lists of structured objects:
        {name: str, library: str | None, branch_id: int}
    """
    enriched: dict[str, list[dict[str, Any]]] = {}

    for ref_type, ref_names in basic_refs.items():
        enriched[ref_type] = []
        for name in ref_names:
            # Check if name has embedded module info (format: "Module::reference_name")
            # This is used for TypeScript regex-detected references where the module
            # is explicitly specified in the code (e.g., $flows.Utilities.list_applications)
            if "::" in name:
                module_name, actual_name = name.split("::", 1)
                branch_id = library_branches.get(module_name, main_branch_id)
                enriched[ref_type].append(
                    {
                        "name": actual_name,
                        "library": module_name,
                        "branch_id": branch_id,
                    }
                )
            else:
                # Fall back to config_index lookup for declarative references
                lookup = config_index.get(name.lower())
                if lookup:
                    _, _, app_ref, is_external = lookup
                    if is_external and app_ref:
                        branch_id = library_branches.get(app_ref, main_branch_id)
                        enriched[ref_type].append(
                            {
                                "name": name,
                                "library": app_ref,
                                "branch_id": branch_id,
                            }
                        )
                    else:
                        enriched[ref_type].append(
                            {
                                "name": name,
                                "library": None,
                                "branch_id": main_branch_id,
                            }
                        )
                else:
                    # Unknown reference - still include it with unknown library
                    enriched[ref_type].append(
                        {
                            "name": name,
                            "library": None,
                            "branch_id": main_branch_id,
                        }
                    )

    return enriched


@click.group()
def explore() -> None:
    """Explore application configurations.

    View and inspect configurations within a Datex Studio application.
    These commands help you understand what functionality an app provides.

    \b
    Examples:
        dxs source explore configs --branch 100
        dxs source explore configs --branch 100 --type grid
        dxs source explore config userGrid --branch 100
        dxs source explore info --branch 100
    """
    pass


@explore.command("info")
@click.option("--branch", "-b", type=int, help="Branch ID")
@pass_context
@require_auth
def info(ctx: DxsContext, branch: int | None) -> None:
    """Show application overview and metadata.

    Displays branch/application information, referenced libraries,
    and configuration counts organized by ownership.

    \b
    Examples:
        dxs source explore info --branch 63393
    """
    branch_id = _resolve_branch_id(ctx, branch)
    client = ApiClient()

    # Start cache session to track cache usage
    start_cache_session()

    ctx.log("Fetching application information...")

    # Get branch info
    branch_data = _get_branch_info(client, branch_id)
    # Use helper for consistent app_name resolution
    app_name = _get_branch_app_name(client, branch_id)

    # Get app definition info
    app_def = branch_data.get("applicationDefinition", {})

    # Get references (direct dependencies)
    ctx.log("Fetching application references...")
    try:
        references_data = client.get(DependencyEndpoints.list(branch_id))
        if not isinstance(references_data, list):
            references_data = [references_data] if references_data else []
        references = [
            ref.get("referenceName") for ref in references_data if ref.get("referenceName")
        ]
    except Exception:
        references = []

    # Build config counts by ownership
    ctx.log("Counting configurations by ownership...")
    owned_counts: dict[str, int] = {}
    referenced_counts: dict[str, int] = {}

    for ctype in CONFIGURATION_TYPES:
        try:
            configs = client.get(ConfigurationEndpoints.list_all(branch_id, ctype))
            if not isinstance(configs, list):
                configs = [configs] if configs else []

            owned = 0
            referenced = 0
            for cfg in configs:
                if _is_config_owned(cfg):
                    owned += 1
                else:
                    referenced += 1

            if owned > 0:
                owned_counts[ctype] = owned
            if referenced > 0:
                referenced_counts[ctype] = referenced
        except Exception:
            pass

    # Warn if app_name is empty (likely a library-heavy app or misconfigured branch)
    display_name = app_name if app_name else f"Branch-{branch_id}"
    if not app_name:
        ctx.log(f"Note: No application reference name found. Using '{display_name}' as identifier.")
        ctx.log("This branch may primarily reference library modules.")

    output = {
        "application": {
            "name": display_name,
            "branch_id": branch_id,
            "description": app_def.get("description") or branch_data.get("description"),
            "type": "Library" if app_def.get("applicationDefinitionTypeId") == 3 else "Application",
            "organization": app_def.get("organization", {}).get("name"),
        },
        "references": references,
        "config_counts": {
            "owned": owned_counts,
            "referenced": referenced_counts,
            "total_owned": sum(owned_counts.values()),
            "total_referenced": sum(referenced_counts.values()),
        },
    }

    # Get cache session info for metadata
    cache_info = end_cache_session() or {}

    ctx.output(single(item=output, semantic_key="info", branch_id=branch_id, **cache_info))


@explore.command("configs")
@click.option("--branch", "-b", type=int, help="Branch ID")
@click.option(
    "--type",
    "-t",
    "config_type",
    type=click.Choice(CONFIGURATION_TYPES, case_sensitive=False),
    help="Filter by configuration type (e.g., grid, form, flow)",
)
@click.option(
    "--search", "-s", type=str, help="Search by reference name or label (case-insensitive)"
)
@click.option("--limit", "-n", type=int, default=0, help="Limit results (0=unlimited)")
@click.option(
    "--owned-only", is_flag=True, help="Only show configs owned by this branch (exclude referenced)"
)
@pass_context
@require_auth
def configs(
    ctx: DxsContext,
    branch: int | None,
    config_type: str | None,
    search: str | None,
    limit: int,
    owned_only: bool,
) -> None:
    """List all configurations in a branch.

    Lists configurations with optional filtering by type or search term.
    Shows reference name, label, type, and access modifier.

    \b
    Examples:
        dxs source explore configs --branch 100
        dxs source explore configs --branch 100 --type grid
        dxs source explore configs --branch 100 --search "user"
        dxs source explore configs --branch 100 --owned-only
    """
    branch_id = _resolve_branch_id(ctx, branch)
    client = ApiClient()

    # Start cache session to track cache usage
    start_cache_session()

    all_configs: list[dict[str, Any]] = []
    type_counts: dict[str, int] = {}

    types_to_fetch = [config_type] if config_type else CONFIGURATION_TYPES

    for ctype in types_to_fetch:
        normalized_type = _normalize_config_type(ctype)
        ctx.log(f"Fetching {normalized_type} configurations...")

        try:
            configs_data = client.get(ConfigurationEndpoints.list_all(branch_id, normalized_type))

            if not isinstance(configs_data, list):
                configs_data = [configs_data] if configs_data else []

            # Filter by ownership if requested
            if owned_only:
                configs_data = [c for c in configs_data if _is_config_owned(c)]

            type_counts[normalized_type] = len(configs_data)

            for config in configs_data:
                all_configs.append(_extract_config_summary(config, normalized_type))

        except Exception as e:
            ctx.log(f"No {normalized_type} configurations found: {e}")
            type_counts[normalized_type] = 0

    # Apply search filter
    if search:
        search_lower = search.lower()
        all_configs = [
            c
            for c in all_configs
            if search_lower in (c.get("referenceName") or "").lower()
            or search_lower in (c.get("label") or "").lower()
        ]

    total_count = len(all_configs)

    if limit > 0:
        all_configs = all_configs[:limit]

    metadata_kwargs: dict[str, Any] = {
        "branch_id": branch_id,
        "total_count": total_count,
    }

    if config_type:
        metadata_kwargs["config_type"] = config_type
    else:
        metadata_kwargs["type_counts"] = {k: v for k, v in type_counts.items() if v > 0}

    if search:
        metadata_kwargs["search"] = search
    if limit > 0:
        metadata_kwargs["limit"] = limit
    if owned_only:
        metadata_kwargs["owned_only"] = True

    # Get cache session info for metadata
    cache_info = end_cache_session() or {}

    ctx.output(
        list_response(
            items=all_configs, semantic_key="configurations", **metadata_kwargs, **cache_info
        )
    )


@explore.command("config")
@click.argument("reference_name")
@click.option("--branch", "-b", type=int, help="Branch ID")
@click.option(
    "--type",
    "-t",
    "config_type",
    type=click.Choice(CONFIGURATION_TYPES, case_sensitive=False),
    help="Configuration type (speeds up lookup if known)",
)
@click.option("--raw", is_flag=True, help="Output only the configuration JSON content")
@pass_context
@require_auth
def config(
    ctx: DxsContext,
    reference_name: str,
    branch: int | None,
    config_type: str | None,
    raw: bool,
) -> None:
    """View a specific configuration's content.

    Fetches the full JSON definition of a configuration by reference name.
    If --type is not specified, searches all types for the reference name.

    \b
    Arguments:
        REFERENCE_NAME  Configuration reference name (e.g., userGrid)

    \b
    Examples:
        dxs source explore config userGrid --branch 100
        dxs source explore config loginFlow --branch 100 --type flow
        dxs source explore config myForm --branch 100 --raw
    """
    branch_id = _resolve_branch_id(ctx, branch)
    client = ApiClient()

    # Start cache session to track cache usage
    start_cache_session()

    found_config: dict[str, Any] | None = None
    found_type: str | None = None
    found_id: int | None = None

    # Try fast lookup via index first
    if not config_type:
        lookup = _lookup_config(client, branch_id, reference_name, ctx)
        if lookup:
            found_type, found_id, _, _ = lookup
            if found_id:
                ctx.log(
                    f"Found {found_type} config with ID {found_id} via index, fetching content..."
                )
                found_config = client.get(
                    ConfigurationEndpoints.get_content(branch_id, found_type, found_id)
                )

    # Fallback: search specified type or all types
    if not found_config:
        types_to_search = [config_type] if config_type else CONFIGURATION_TYPES

        for ctype in types_to_search:
            normalized_type = _normalize_config_type(ctype)
            ctx.log(f"Searching {normalized_type} configurations...")

            try:
                configs_list = client.get(
                    ConfigurationEndpoints.list_all(branch_id, normalized_type)
                )

                if not isinstance(configs_list, list):
                    configs_list = [configs_list] if configs_list else []

                ref_lower = reference_name.lower()
                for cfg in configs_list:
                    if cfg.get("referenceName", "").lower() == ref_lower:
                        found_id = cfg.get("id")
                        found_type = normalized_type
                        break

                if found_id:
                    ctx.log(
                        f"Found {normalized_type} config with ID {found_id}, fetching content..."
                    )
                    found_config = client.get(
                        ConfigurationEndpoints.get_content(branch_id, normalized_type, found_id)
                    )
                    break

            except Exception:
                continue

    if not found_config:
        raise ValidationError(
            message=f"Configuration '{reference_name}' not found",
            suggestions=[
                "Check the reference name spelling",
                "Use 'dxs source explore configs' to list available configurations",
                "Specify --type if you know the configuration type",
            ],
        )

    if raw:
        content = (
            found_config.get("config")
            or found_config.get("json")
            or found_config.get("json_content")
            or {}
        )
        cache_info = end_cache_session() or {}
        ctx.output(single(item=content, semantic_key="config", **cache_info))
        return

    # Transform API response using the output model
    config_output = ConfigurationOutput.from_api(found_config)

    # Apply code-to-literal for YAML multiline display
    content_dict = convert_code_to_literal(config_output.content)

    # Merge config metadata into response metadata
    config_metadata = config_output.metadata.to_metadata_dict()

    # Get cache session info for metadata
    cache_info = end_cache_session() or {}

    ctx.output(
        single(
            item=content_dict,
            semantic_key="configuration",
            config_type=found_type,
            reference_name=reference_name,
            **config_metadata,
            **cache_info,
        )
    )


@explore.command("summary")
@click.argument("reference_name")
@click.option("--branch", "-b", type=int, help="Branch ID")
@click.option(
    "--type",
    "-t",
    "config_type",
    type=click.Choice(CONFIGURATION_TYPES, case_sensitive=False),
    help="Configuration type (speeds up lookup if known)",
)
@click.option("--owned-only", is_flag=True, help="Only match configs owned by this branch")
@pass_context
@require_auth
def summary(
    ctx: DxsContext,
    reference_name: str,
    branch: int | None,
    config_type: str | None,
    owned_only: bool,
) -> None:
    """Show structural summary of a configuration.

    Extracts key structural elements based on configuration type:
    - grid: datasource, columns, toolbar buttons, row actions
    - form: fields, submit/cancel flows
    - flow: in/out params, called flows and datasources
    - etc.

    \b
    Examples:
        dxs source explore summary equipment_grid --branch 61135
        dxs source explore summary create_order_flow --branch 100 --type flow
        dxs source explore summary shell --branch 100 --owned-only
    """
    branch_id = _resolve_branch_id(ctx, branch)
    client = ApiClient()

    # Start cache session to track cache usage
    start_cache_session()

    # Use index for fast lookup
    lookup = _lookup_config(client, branch_id, reference_name, ctx)

    found_type: str | None = None
    found_id: int | None = None
    found_app: str = ""
    found_is_external: bool = False

    if lookup:
        found_type, found_id, found_app, found_is_external = lookup
    elif config_type:
        found_type = config_type

    if not found_type:
        raise ValidationError(
            message=f"Configuration '{reference_name}' not found",
            suggestions=[
                "Check the reference name spelling",
                "Use 'dxs source explore configs' to list available configurations",
            ],
        )

    # Check ownership filter (external configs are not owned by this branch)
    if owned_only and found_is_external:
        raise ValidationError(
            message=f"Configuration '{reference_name}' is from '{found_app}', not owned by this branch",
            suggestions=[
                "Remove --owned-only to see this configuration",
                f"Use --branch on the '{found_app}' branch instead",
            ],
        )

    if found_id:
        found_config = client.get(
            ConfigurationEndpoints.get_content(branch_id, found_type, found_id)
        )
    else:
        configs_list = client.get(ConfigurationEndpoints.list_all(branch_id, found_type))
        if not isinstance(configs_list, list):
            configs_list = [configs_list] if configs_list else []

        ref_lower = reference_name.lower()
        for cfg in configs_list:
            if cfg.get("referenceName", "").lower() == ref_lower:
                if owned_only and not _is_config_owned(cfg):
                    continue
                found_id = cfg.get("id")
                break

        if not found_id:
            raise ValidationError(message=f"Configuration '{reference_name}' not found")

        found_config = client.get(
            ConfigurationEndpoints.get_content(branch_id, found_type, found_id)
        )

    type_summary = _extract_type_summary(found_config, found_type)

    output = {
        "referenceName": reference_name,
        "configType": found_type,
        "label": found_config.get("label"),
        **type_summary,
    }

    # Get cache session info for metadata
    cache_info = end_cache_session() or {}

    ctx.output(single(item=output, semantic_key="summary", branch_id=branch_id, **cache_info))


def _enrich_with_library(
    basic_refs: dict[str, list[str]],
    config_index: dict[str, tuple[str, int, str, bool]],
    library_branches: dict[str, int],
    main_branch_id: int,
) -> dict[str, list[dict[str, Any]]]:
    """Convert reference names to structured objects with library info.

    Args:
        basic_refs: Reference names grouped by type
        config_index: Lookup dict: ref_name_lower -> (type, id, app_ref, is_external)
        library_branches: Library name -> branch_id mapping
        main_branch_id: Branch ID of the main application

    Returns:
        Dict with same keys but values are lists of {name, library} objects
    """
    enriched: dict[str, list[dict[str, Any]]] = {}

    for ref_type, ref_names in basic_refs.items():
        enriched[ref_type] = []
        for name in ref_names:
            # Check if name has embedded module info (format: "Module::reference_name")
            # This is used for TypeScript regex-detected references where the module
            # is explicitly specified in the code (e.g., $flows.Utilities.list_applications)
            if "::" in name:
                module_name, actual_name = name.split("::", 1)
                enriched[ref_type].append(
                    {
                        "name": actual_name,
                        "library": module_name,
                    }
                )
            else:
                # Fall back to config_index lookup for declarative references
                lookup = config_index.get(name.lower())
                if lookup:
                    _, _, app_ref, is_external = lookup
                    if is_external and app_ref:
                        enriched[ref_type].append(
                            {
                                "name": name,
                                "library": app_ref,
                            }
                        )
                    else:
                        enriched[ref_type].append(
                            {
                                "name": name,
                                "library": None,  # Local/owned config
                            }
                        )
                else:
                    # Reference not found in index - include without library info
                    enriched[ref_type].append(
                        {
                            "name": name,
                            "library": None,
                        }
                    )

    return enriched


def _find_base_directory(file_path: Path) -> Path | None:
    """Find the base directory containing libraries.yaml by walking up from file_path."""
    current = file_path.parent
    for _ in range(10):  # Limit search depth
        if (current / "libraries.yaml").exists():
            return current
        if current.parent == current:  # Reached root
            break
        current = current.parent
    return None


def _trace_single_file(
    file_path: Path,
) -> dict[str, Any]:
    """Trace references from a single YAML config file.

    Attempts to find the base directory by walking up the path to locate
    libraries.yaml, then loads the config index for library attribution.

    Args:
        file_path: Full path to the YAML config file

    Returns:
        Trace output dict with references including library info
    """
    from dxs.commands.document import (
        _build_config_index_from_filesystem,
        _load_libraries_yaml,
        _scan_config_directory,
    )

    # Read the YAML file
    with open(file_path) as f:
        data = yaml.safe_load(f)

    # Extract metadata and raw_config
    reference_name = data.get("reference_name", file_path.stem)
    config_type = data.get("config_type", file_path.parent.name)
    raw_config = data.get("raw_config", {})

    # Try to find base directory for library lookup
    base_dir = _find_base_directory(file_path)

    if base_dir:
        # Load config index and library mappings
        try:
            main_branch_id, library_branches = _load_libraries_yaml(base_dir)
            configs = _scan_config_directory(base_dir)
            config_index = _build_config_index_from_filesystem(configs)

            # Extract references with config index
            basic_refs = _extract_all_references(raw_config, config_type, config_index)

            # Enrich with library info
            references: dict[str, Any] = _enrich_with_library(
                basic_refs, config_index, library_branches, main_branch_id
            )
        except Exception:
            # Fall back to basic extraction
            references = _extract_all_references(raw_config, config_type, config_index={})
    else:
        # No base directory found - basic extraction only
        references = _extract_all_references(raw_config, config_type, config_index={})

    return {
        "reference_name": reference_name,
        "config_type": config_type,
        "source_file": str(file_path),
        "references": references,
    }


def _trace_batch(
    ctx: DxsContext,
    directory: Path,
) -> dict[str, Any]:
    """Batch generate context files for all YAML configs in a directory structure.

    Walks the document build directory, generates context for each config file,
    and saves results alongside as <name>.context.yaml. Context files contain
    both structural information (from summary extraction) and dependency
    references (from trace extraction) in a single file.

    Args:
        ctx: DxsContext for logging
        directory: Document build output directory

    Returns:
        Summary dict with counts and any errors
    """
    import time

    from dxs.commands.document import (
        _build_config_index_from_filesystem,
        _load_libraries_yaml,
        _scan_config_directory,
    )

    start_time = time.time()

    # Load library mappings for library info
    try:
        main_branch_id, library_branches = _load_libraries_yaml(directory)
    except ValidationError:
        # No libraries.yaml - can still process but without library info
        main_branch_id = 0
        library_branches = {}
        ctx.log("Warning: libraries.yaml not found, library info will be limited")

    # Scan filesystem for configs (excluding auxiliary files)
    ctx.log("Scanning filesystem for configs...")
    all_configs = _scan_config_directory(directory)
    configs = [
        (p, r, t, lib, b)
        for p, r, t, lib, b in all_configs
        if not p.name.endswith((".trace.yaml", ".context.yaml"))
    ]
    total_files = len(configs)
    ctx.log(
        f"Found {total_files} config files (excluded {len(all_configs) - total_files} auxiliary files)"
    )

    # Build config index for type classification
    ctx.log("Building configuration index...")
    config_index = _build_config_index_from_filesystem(configs)

    # Process each config
    succeeded = 0
    failed = 0
    errors: list[dict[str, str]] = []

    ctx.log("Generating context files...")
    for i, (path, ref_name, config_type, lib_name, _branch_id) in enumerate(configs):
        # Progress reporting
        if (i + 1) % 100 == 0 or (i + 1) == total_files:
            ctx.log(f"  Progress: {i + 1}/{total_files} ({(i + 1) / total_files * 100:.1f}%)")

        try:
            # Load the config
            with open(path) as f:
                data = yaml.safe_load(f)

            raw_config = data.get("raw_config", {})

            # Generate combined context data
            context_data = _generate_context_data(
                config=raw_config,
                config_type=config_type,
                ref_name=ref_name,
                source_file=str(path.relative_to(directory)),
                library=lib_name,
                config_index=config_index,
                library_branches=library_branches,
                main_branch_id=main_branch_id,
            )

            # Write context file alongside original
            context_path = path.with_suffix(".context.yaml")
            with open(context_path, "w") as f:
                yaml.dump(
                    context_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
                )

            succeeded += 1

        except Exception as e:
            failed += 1
            errors.append(
                {
                    "file": str(path.relative_to(directory)),
                    "error": str(e),
                }
            )

    elapsed = time.time() - start_time

    return {
        "total_files": total_files,
        "succeeded": succeeded,
        "failed": failed,
        "elapsed_seconds": round(elapsed, 2),
        "output_directory": str(directory),
        "errors": errors if errors else None,
    }


@explore.command("trace")
@click.argument("reference", required=False)
@click.option("--branch", "-b", type=int, help="Branch ID (for API mode)")
@click.option("--offline", is_flag=True, help="Offline mode - REFERENCE is a file path")
@click.option(
    "--batch",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Batch process all .yaml files in directory (requires --offline)",
)
@click.option(
    "--type",
    "-t",
    "config_type",
    type=click.Choice(CONFIGURATION_TYPES, case_sensitive=False),
    help="Configuration type (speeds up lookup if known)",
)
@pass_context
def trace(
    ctx: DxsContext,
    reference: str | None,
    branch: int | None,
    offline: bool,
    batch: str | None,
    config_type: str | None,
) -> None:
    """Show what configurations this config references.

    Traces dependencies to datasources, flows, forms, editors, etc.
    All references include their source library/module.

    \b
    Three modes:
    - API mode: Fetches from API (requires authentication)
    - Offline mode: Reads a single YAML file
    - Batch mode: Processes all files in a directory

    \b
    Examples:
        # API mode
        dxs source explore trace equipment_grid --branch 61135

        # Offline mode (single file)
        dxs source explore trace ./exploration/Footprint/23403/local/hub/orders_hub.yaml --offline

        # Batch mode (all files, saves .trace.yaml alongside each)
        dxs source explore trace --offline --batch ./exploration/Footprint/23403/
    """
    # Batch mode: process all files in directory
    if batch:
        check_restricted_mode_for_option("--batch", "writes .context.yaml files to the filesystem")
        if not offline:
            raise ValidationError(
                message="--batch requires --offline flag",
                suggestions=["Use: dxs source explore trace --offline --batch <directory>"],
            )
        if reference:
            raise ValidationError(
                message="--batch mode does not accept a REFERENCE argument",
                suggestions=["Use: dxs source explore trace --offline --batch <directory>"],
            )
        output = _trace_batch(ctx, Path(batch))
        ctx.output(single(item=output, semantic_key="trace_batch", mode="batch"))
        return

    # Offline mode: trace a single file
    if offline:
        if not reference:
            raise ValidationError(
                message="--offline mode requires a file path",
                suggestions=[
                    "Provide full path: dxs source explore trace ./path/to/config.yaml --offline"
                ],
            )
        file_path = Path(reference)
        if not file_path.exists():
            raise ValidationError(message=f"File not found: {reference}")
        if file_path.suffix != ".yaml":
            raise ValidationError(
                message=f"Expected .yaml file, got: {reference}",
                suggestions=["Provide path to a YAML config file from document build output"],
            )
        output = _trace_single_file(file_path)
        ctx.output(single(item=output, semantic_key="trace", mode="offline"))
        return

    # API mode: fetch from API (requires authentication)
    if not reference:
        raise ValidationError(
            message="API mode requires a reference name",
            suggestions=[
                "Provide a config name: dxs source explore trace <config_name> --branch <id>",
                "Or use --offline for filesystem mode",
            ],
        )

    from dxs.core.auth.decorators import get_access_token

    # Check auth before proceeding (supports both env vars and file cache)
    try:
        get_access_token()
    except Exception:
        from dxs.utils.errors import AuthenticationError

        raise AuthenticationError(
            message="Not authenticated. Please log in first.",
            code="DXS-AUTH-002",
            suggestions=[
                "Run 'dxs auth login' to authenticate",
                "Set DXS_ACCESS_TOKEN environment variable",
                "Or use --offline to trace from filesystem",
            ],
        )

    reference_name = reference

    branch_id = _resolve_branch_id(ctx, branch)
    client = ApiClient()

    # Start cache session to track cache usage
    start_cache_session()

    # Get branch status for caching decisions
    branch_info = _get_branch_info(client, branch_id)
    branch_status = branch_info.get("applicationStatusId", 0)

    lookup = _lookup_config(client, branch_id, reference_name, ctx)

    found_type: str | None = None
    found_id: int | None = None

    if lookup:
        found_type, found_id, _, _ = lookup
    elif config_type:
        found_type = config_type

    if not found_type:
        raise ValidationError(
            message=f"Configuration '{reference_name}' not found",
            suggestions=[
                "Check the reference name spelling",
                "Use 'dxs source explore configs' to list available configurations",
            ],
        )

    if found_id:
        found_config = _get_config_content_cached(
            client, branch_id, found_type, found_id, branch_status
        )
        if not found_config:
            raise ValidationError(message=f"Failed to fetch configuration '{reference_name}'")
    else:
        configs_list = client.get(ConfigurationEndpoints.list_all(branch_id, found_type))
        if not isinstance(configs_list, list):
            configs_list = [configs_list] if configs_list else []

        ref_lower = reference_name.lower()
        for cfg in configs_list:
            if cfg.get("referenceName", "").lower() == ref_lower:
                found_id = cfg.get("id")
                break

        if not found_id:
            raise ValidationError(message=f"Configuration '{reference_name}' not found")

        found_config = _get_config_content_cached(
            client, branch_id, found_type, found_id, branch_status
        )
        if not found_config:
            raise ValidationError(message=f"Failed to fetch configuration '{reference_name}'")

    config_index = _build_config_index(client, branch_id, ctx)
    basic_refs = _get_references_cached(
        found_config, found_type, found_id, branch_id, branch_status, config_index
    )

    # Always enrich references with library info
    from dxs.commands.document import _fetch_library_branches

    library_branches, _ = _fetch_library_branches(client, branch_id)
    references: dict[str, Any] = _enrich_with_library(
        basic_refs, config_index, library_branches, branch_id
    )

    output = {
        "referenceName": reference_name,
        "configType": found_type,
        "references": references,
    }

    # Get cache session info for metadata
    cache_info = end_cache_session() or {}

    ctx.output(
        single(item=output, semantic_key="trace", branch_id=branch_id, mode="api", **cache_info)
    )


@explore.command("graph")
@click.option("--branch", "-b", type=int, required=True, help="Branch ID")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Output directory (optional, prints to stdout if not set)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["mermaid", "yaml"]),
    default="mermaid",
    help="Output format",
)
@click.option("--owned-only", is_flag=True, help="Only include configs owned by this branch")
@click.option("--max-depth", "-d", type=int, default=3, help="Maximum traversal depth from shell")
@pass_context
@require_auth
def graph(
    ctx: DxsContext,
    branch: int,
    output_dir: str | None,
    output_format: str,
    owned_only: bool,
    max_depth: int,
) -> None:
    """Generate a dependency graph of the application.

    Creates a visual map showing how configurations connect:
    shell -> hubs -> grids/forms -> flows -> datasources

    \b
    Examples:
        dxs source explore graph --branch 63393
        dxs source explore graph --branch 63393 --format mermaid --output-dir ./docs
        dxs source explore graph --branch 100 --owned-only
    """
    branch_id = branch
    client = ApiClient()

    # Start cache session to track cache usage
    start_cache_session()

    # Get branch status for caching decisions
    branch_info = _get_branch_info(client, branch_id)
    branch_status = branch_info.get("applicationStatusId", 0)

    app_name = _get_branch_app_name(client, branch_id)
    ctx.log(f"Building dependency graph for {app_name}...")

    # Build the config index
    index = _build_config_index(client, branch_id, ctx)

    # Track nodes and edges
    nodes: dict[str, dict[str, Any]] = {}  # ref_name -> {type, label, owned}
    edges: list[tuple[str, str, str]] = []  # (from, to, label)
    visited: set[str] = set()

    def add_node(ref_name: str, config_type: str, label: str | None, owned: bool) -> None:
        if ref_name not in nodes:
            nodes[ref_name] = {"type": config_type, "label": label, "owned": owned}

    def traverse(ref_name: str, depth: int = 0) -> None:
        if depth > max_depth or ref_name.lower() in visited:
            return
        visited.add(ref_name.lower())

        lookup = index.get(ref_name.lower())
        if not lookup:
            return

        config_type, config_id, cfg_app, cfg_is_external = lookup
        is_owned = not cfg_is_external

        if owned_only and not is_owned:
            return

        if not config_id:
            return

        cfg = _get_config_content_cached(client, branch_id, config_type, config_id, branch_status)
        if not cfg:
            return

        label = cfg.get("label") or cfg.get("title") or ref_name
        add_node(ref_name, config_type, label, is_owned)

        # Extract references (with caching)
        refs = _get_references_cached(cfg, config_type, config_id, branch_id, branch_status, index)

        for ref_type, ref_list in refs.items():
            edge_label = ref_type.rstrip("s")  # flows -> flow
            for ref in ref_list:
                ref_lookup = index.get(ref.lower())
                if ref_lookup:
                    ref_cfg_type, _, ref_app, ref_is_external = ref_lookup
                    ref_owned = not ref_is_external
                    if owned_only and not ref_owned:
                        continue
                    add_node(ref, ref_cfg_type, None, ref_owned)
                    edges.append((ref_name, ref, edge_label))
                    traverse(ref, depth + 1)

    # Start from shells
    ctx.log("Finding entry points (shells)...")
    try:
        shells = client.get(ConfigurationEndpoints.list_all(branch_id, "shell"))
        if not isinstance(shells, list):
            shells = [shells] if shells else []

        for shell in shells:
            shell_is_external = shell.get("isExternal", False)
            if owned_only and shell_is_external:
                continue
            ref_name = shell.get("referenceName", "")
            if ref_name:
                # Add shell node immediately - don't rely on traverse to add it
                label = shell.get("title") or shell.get("label") or ref_name
                is_owned = not shell_is_external
                add_node(ref_name, "shell", label, is_owned)
                traverse(ref_name)
    except Exception as e:
        ctx.log(f"Error fetching shells: {e}")

    # Generate output
    if output_format == "mermaid":
        lines = ["graph TD"]

        # Add node definitions with styling
        for ref_name, info in nodes.items():
            safe_name = ref_name.replace("-", "_").replace(".", "_")
            label = info.get("label") or ref_name
            config_type = info["type"]
            style = ""

            # Style by type
            if config_type == "shell":
                style = ":::shell"
            elif config_type == "hub":
                style = ":::hub"
            elif config_type == "grid":
                style = ":::grid"
            elif config_type == "form":
                style = ":::form"
            elif config_type in ("flow", "frontendflow"):
                style = ":::flow"
            elif config_type in ("datasource", "footprintdatasource"):
                style = ":::datasource"

            lines.append(f"    {safe_name}[{label}]{style}")

        # Add edges
        for from_node, to_node, label in edges:
            safe_from = from_node.replace("-", "_").replace(".", "_")
            safe_to = to_node.replace("-", "_").replace(".", "_")
            lines.append(f"    {safe_from} -->|{label}| {safe_to}")

        # Add style definitions
        lines.extend(
            [
                "",
                "    classDef shell fill:#e1f5fe,stroke:#01579b",
                "    classDef hub fill:#f3e5f5,stroke:#4a148c",
                "    classDef grid fill:#e8f5e9,stroke:#1b5e20",
                "    classDef form fill:#fff3e0,stroke:#e65100",
                "    classDef flow fill:#fce4ec,stroke:#880e4f",
                "    classDef datasource fill:#e3f2fd,stroke:#0d47a1",
            ]
        )

        graph_output = "\n".join(lines)
    else:
        # YAML format
        graph_output = yaml.dump(
            {
                "nodes": nodes,
                "edges": [{"from": e[0], "to": e[1], "type": e[2]} for e in edges],
            },
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        ext = ".md" if output_format == "mermaid" else ".yaml"
        file_path = out_path / f"dependency-graph{ext}"

        content = graph_output
        if output_format == "mermaid":
            content = f"# {app_name} Dependency Graph\n\n```mermaid\n{graph_output}\n```\n"

        with open(file_path, "w") as f:
            f.write(content)

        # Get cache session info for metadata
        cache_info = end_cache_session() or {}

        ctx.output(
            single(
                item={"file": str(file_path), "nodes": len(nodes), "edges": len(edges)},
                semantic_key="graph",
                branch_id=branch_id,
                **cache_info,
            )
        )
    else:
        # Get cache session info for metadata
        cache_info = end_cache_session() or {}

        # Print to stdout
        ctx.output(
            single(
                item={"graph": graph_output, "nodes": len(nodes), "edges": len(edges)},
                semantic_key="graph",
                branch_id=branch_id,
                **cache_info,
            )
        )


@explore.command("cache")
@click.option("--clear", is_flag=True, help="Clear entire cache")
@click.option("--clear-branch", type=int, help="Clear cache for specific branch")
@click.option("--stats", is_flag=True, help="Show cache statistics (default)")
@pass_context
def cache_cmd(
    ctx: DxsContext,
    clear: bool,
    clear_branch: int | None,
    stats: bool,
) -> None:
    """Manage the explore command cache.

    The cache stores configuration data for immutable branches
    (INACTIVE, PUBLISHED_MAIN, WORKSPACE_HISTORY) to avoid redundant API calls
    across CLI invocations.

    Main and WorkspaceActive (feature) branches are never cached
    as they are mutable.

    \b
    Examples:
        dxs source explore cache             # Show cache stats
        dxs source explore cache --stats     # Show cache stats
        dxs source explore cache --clear     # Clear entire cache
        dxs source explore cache --clear-branch 63393  # Clear specific branch
    """
    cache = get_cache()

    if clear:
        counts = cache.clear_all()
        total = sum(counts.values())
        ctx.output(
            single(
                item={"cleared": counts, "total_entries": total},
                semantic_key="cache_cleared",
            )
        )
    elif clear_branch:
        count = cache.clear_branch(clear_branch)
        ctx.output(
            single(
                item={"branch_id": clear_branch, "entries_cleared": count},
                semantic_key="branch_cache_cleared",
            )
        )
    else:
        # Default: show stats
        stats_data = cache.get_stats()
        ctx.output(single(item=stats_data, semantic_key="cache_stats"))


# =============================================================================
# Analysis Workflow Commands
# =============================================================================


def _load_dependency_graph(graph_path: Path) -> Any:
    """Load dependency graph from YAML file."""
    from dxs.core.graph import DependencyGraph

    if not graph_path.exists():
        raise ValidationError(
            message=f"Graph file not found: {graph_path}",
            suggestions=[
                "Run 'dxs source document graph' to generate the graph first",
                "Check the path is correct",
            ],
        )

    with open(graph_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return DependencyGraph.from_dict(data)


def _bfs_from_roots(graph: Any, roots: list[str], max_depth: int = -1) -> dict[str, dict[str, Any]]:
    """BFS traversal from root nodes to find all reachable components.

    Returns dict of ref_name_lower -> node info with depth.
    """
    from collections import deque

    adj = graph.get_adjacency_list()
    visited: dict[str, dict[str, Any]] = {}
    queue: deque[tuple[str, int]] = deque()

    # Initialize with roots
    for root in roots:
        root_lower = root.lower()
        if root_lower in graph.nodes:
            queue.append((root_lower, 0))
            node = graph.nodes[root_lower]
            visited[root_lower] = {
                "reference_name": node.reference_name,
                "config_type": node.config_type,
                "config_id": node.config_id,
                "branch_id": node.branch_id,
                "application_ref_name": node.application_ref_name,
                "is_external": node.is_external,
                "depth": 0,
            }

    # BFS
    while queue:
        current, depth = queue.popleft()
        next_depth = depth + 1

        if max_depth >= 0 and next_depth > max_depth:
            continue

        for neighbor in adj.get(current, []):
            if neighbor not in visited:
                node = graph.nodes.get(neighbor)
                if node:
                    visited[neighbor] = {
                        "reference_name": node.reference_name,
                        "config_type": node.config_type,
                        "config_id": node.config_id,
                        "branch_id": node.branch_id,
                        "application_ref_name": node.application_ref_name,
                        "is_external": node.is_external,
                        "depth": next_depth,
                    }
                    queue.append((neighbor, next_depth))

    return visited


def _check_analysis_exists(
    base_dir: Path, library: str, branch_id: int, config_type: str, name: str
) -> bool:
    """Check if an analysis file exists for a component."""
    analysis_path = base_dir / library / str(branch_id) / config_type / f"{name}.analysis.md"
    return analysis_path.exists()


def _check_has_code(config_path: Path) -> tuple[bool, int]:
    """Check if config has code and count lines.

    Code can be in multiple locations:
    - raw_config.code (simple flows)
    - raw_config.nodes[*].stepConfig.executeCodeConfig.code (step-based flows)
    """
    if not config_path.exists():
        return False, 0

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        raw_config = data.get("raw_config", {})

        # Check direct code field
        code = raw_config.get("code", "")
        if code and isinstance(code, str) and len(code.strip()) > 0:
            return True, code.count("\n") + 1

        # Check nodes for step-based flows
        nodes = raw_config.get("nodes", [])
        total_lines = 0
        has_code = False

        for node in nodes:
            step_config = node.get("stepConfig", {})
            exec_config = step_config.get("executeCodeConfig", {})
            node_code = exec_config.get("code", "")
            if node_code and isinstance(node_code, str) and len(node_code.strip()) > 0:
                has_code = True
                total_lines += node_code.count("\n") + 1

        if has_code:
            return True, total_lines

    except Exception:
        pass

    return False, 0


def _determine_priority(config_type: str, depth: int, has_code: bool) -> str:
    """Determine priority based on component type and characteristics."""
    if config_type in ("hub", "shell"):
        return "critical"
    if config_type == "flow" and has_code:
        return "high"
    if config_type in ("grid", "form", "editor"):
        return "high" if depth <= 2 else "medium"
    if config_type == "flow":
        return "medium"
    if config_type in ("datasource", "selector"):
        return "low"
    return "low"


@explore.command("manifest")
@click.option(
    "--graph",
    "-g",
    "graph_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to dependency-graph.yaml file",
)
@click.option(
    "--roots",
    "-r",
    required=True,
    help="Comma-separated list of root component names (e.g., sales_order_hub,waves_hub)",
)
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(exists=True),
    help="Base directory for checking analysis files (defaults to graph's parent/parent)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (prints to stdout if not set)",
)
@click.option(
    "--max-depth",
    type=int,
    default=-1,
    help="Maximum traversal depth (-1 for unlimited)",
)
@click.option(
    "--section",
    help="Section name for the manifest (e.g., 'outbound')",
)
@pass_context
def manifest(
    ctx: DxsContext,
    graph_path: str,
    roots: str,
    base_dir: str | None,
    output: str | None,
    max_depth: int,
    section: str | None,
) -> None:
    """Generate a component manifest from the dependency graph.

    Performs BFS from root components to find all reachable configs,
    checks for existing analysis files, and outputs a prioritized manifest.

    \b
    Examples:
        dxs source explore manifest \\
          --graph ./exploration/Footprint/23403/graph/dependency-graph.yaml \\
          --roots sales_order_hub,waves_hub \\
          --section outbound \\
          --output outbound_manifest.yaml
    """
    graph_file = Path(graph_path)
    graph = _load_dependency_graph(graph_file)

    # Determine base directory for analysis checks
    if base_dir:
        base_path = Path(base_dir)
    else:
        # Default: graph is at {base}/graph/dependency-graph.yaml
        base_path = graph_file.parent.parent

    # Parse roots
    root_list = [r.strip() for r in roots.split(",") if r.strip()]
    if not root_list:
        raise ValidationError(
            message="No roots specified",
            suggestions=["Provide at least one root: --roots hub1,hub2"],
        )

    ctx.log(f"Building manifest from {len(root_list)} root(s): {', '.join(root_list)}")

    # BFS to find all reachable components
    reachable = _bfs_from_roots(graph, root_list, max_depth)
    ctx.log(f"Found {len(reachable)} reachable components")

    # Build manifest with analysis status and priorities
    components: list[dict[str, Any]] = []
    by_type: dict[str, int] = {}
    analyzed_count = 0

    for _ref_lower, info in reachable.items():
        config_type = info["config_type"]
        ref_name = info["reference_name"]
        branch_id = info["branch_id"]
        app_ref = info["application_ref_name"]
        depth = info["depth"]

        # Determine library name
        library = (
            app_ref
            if app_ref
            else next(
                (name for name, bid in graph.library_branches.items() if bid == branch_id),
                "Unknown",
            )
        )

        # Build config path
        config_path = base_path / library / str(branch_id) / config_type / f"{ref_name}.yaml"

        # Check for analysis file
        analysis_exists = _check_analysis_exists(
            base_path, library, branch_id, config_type, ref_name
        )
        if analysis_exists:
            analyzed_count += 1

        # Check for code
        has_code, code_lines = _check_has_code(config_path)

        # Determine priority
        priority = _determine_priority(config_type, depth, has_code)

        # Count by type
        by_type[config_type] = by_type.get(config_type, 0) + 1

        components.append(
            {
                "name": ref_name,
                "type": config_type,
                "depth": depth,
                "library": library,
                "branch_id": branch_id,
                "config_path": str(config_path.relative_to(base_path))
                if config_path.is_relative_to(base_path)
                else str(config_path),
                "analysis_exists": analysis_exists,
                "has_code": has_code,
                "code_lines": code_lines if has_code else None,
                "priority": priority,
            }
        )

    # Sort by priority then depth
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    components.sort(key=lambda c: (priority_order.get(c["priority"], 99), c["depth"], c["name"]))

    # Build manifest output
    manifest_data = {
        "roots": root_list,
        "section": section,
        "base_dir": str(base_path),
        "total_components": len(components),
        "analyzed": analyzed_count,
        "needs_analysis": len(components) - analyzed_count,
        "by_type": dict(sorted(by_type.items())),
        "by_priority": {
            "critical": sum(1 for c in components if c["priority"] == "critical"),
            "high": sum(1 for c in components if c["priority"] == "high"),
            "medium": sum(1 for c in components if c["priority"] == "medium"),
            "low": sum(1 for c in components if c["priority"] == "low"),
        },
        "components": components,
    }

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(
                manifest_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
        ctx.log(f"Manifest written to: {out_path}")
        ctx.output(
            single(
                item={
                    "file": str(out_path),
                    "total": len(components),
                    "analyzed": analyzed_count,
                    "needs_analysis": len(components) - analyzed_count,
                },
                semantic_key="manifest",
            )
        )
    else:
        ctx.output(single(item=manifest_data, semantic_key="manifest"))


@explore.command("extract-code")
@click.option(
    "--manifest",
    "-m",
    "manifest_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to manifest YAML file",
)
@click.option(
    "--output",
    "-o",
    "output_dir",
    type=click.Path(),
    required=True,
    help="Output directory for extracted code files",
)
@click.option(
    "--flows-only",
    is_flag=True,
    help="Only extract code from flow configs",
)
@pass_context
@restrict_in_restricted_mode("writes code files to the filesystem")
def extract_code(
    ctx: DxsContext,
    manifest_path: str,
    output_dir: str,
    flows_only: bool,
) -> None:
    """Extract code blocks from config files into separate .code.ts files.

    Reads the manifest and extracts raw_config.code sections from
    flows (and optionally other config types) into standalone files.

    \b
    Examples:
        dxs source explore extract-code \\
          --manifest outbound_manifest.yaml \\
          --output ./exploration/Footprint/23403/code/
    """
    # Load manifest
    manifest_file = Path(manifest_path)
    with open(manifest_file, encoding="utf-8") as f:
        manifest_data = yaml.safe_load(f)

    base_dir = Path(manifest_data.get("base_dir", "."))
    components = manifest_data.get("components", [])
    out_path = Path(output_dir)

    extracted = 0
    skipped = 0
    errors = 0
    files_created: list[str] = []

    for comp in components:
        config_type = comp["type"]

        # Skip non-flows if flows_only
        if flows_only and config_type not in ("flow", "frontendflow"):
            continue

        # Skip if no code
        if not comp.get("has_code"):
            skipped += 1
            continue

        config_path = base_dir / comp["config_path"]
        if not config_path.exists():
            ctx.log(f"Warning: Config not found: {config_path}")
            errors += 1
            continue

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            raw_config = config_data.get("raw_config", {})

            # Extract code from multiple possible locations
            code_blocks: list[str] = []

            # Direct code field
            direct_code = raw_config.get("code", "")
            if direct_code and isinstance(direct_code, str) and direct_code.strip():
                code_blocks.append(direct_code)

            # Node-based code (step flows)
            nodes = raw_config.get("nodes", [])
            for node in nodes:
                node_id = node.get("id", "unknown")
                step_config = node.get("stepConfig", {})
                exec_config = step_config.get("executeCodeConfig", {})
                node_code = exec_config.get("code", "")
                if node_code and isinstance(node_code, str) and node_code.strip():
                    # Add node marker for multi-step flows
                    if len(nodes) > 1:
                        code_blocks.append(f"// === Step: {node_id} ===\n{node_code}")
                    else:
                        code_blocks.append(node_code)

            if not code_blocks:
                skipped += 1
                continue

            code = "\n\n".join(code_blocks)

            # Extract parameters for header comment
            in_params = raw_config.get("inParams", [])
            out_params = raw_config.get("outParams", [])

            # Build header comment
            header_lines = [
                f"// Flow: {comp['name']}",
                f"// Library: {comp['library']}",
                f"// Config: {comp['config_path']}",
                "//",
            ]

            if in_params:
                header_lines.append("// Input Parameters:")
                for p in in_params:
                    p_name = p.get("name", "?")
                    p_type = p.get("dataType", "any")
                    p_required = "required" if p.get("isRequired") else "optional"
                    header_lines.append(f"//   {p_name}: {p_type} ({p_required})")

            if out_params:
                header_lines.append("// Output Parameters:")
                for p in out_params:
                    p_name = p.get("name", "?")
                    p_type = p.get("dataType", "any")
                    header_lines.append(f"//   {p_name}: {p_type}")

            header_lines.append("")

            # Write code file
            code_dir = out_path / comp["library"] / str(comp["branch_id"])
            code_dir.mkdir(parents=True, exist_ok=True)
            code_file = code_dir / f"{comp['name']}.code.ts"

            with open(code_file, "w", encoding="utf-8") as f:
                f.write("\n".join(header_lines))
                f.write(code)

            files_created.append(str(code_file.relative_to(out_path)))
            extracted += 1

        except Exception as e:
            ctx.log(f"Error extracting {comp['name']}: {e}")
            errors += 1

    ctx.log(f"Extracted: {extracted}, Skipped: {skipped}, Errors: {errors}")

    ctx.output(
        single(
            item={
                "output_dir": str(out_path),
                "extracted": extracted,
                "skipped": skipped,
                "errors": errors,
                "files": files_created[:20] if len(files_created) > 20 else files_created,
                "total_files": len(files_created),
            },
            semantic_key="extract_code",
        )
    )


@explore.command("verify")
@click.option(
    "--manifest",
    "-m",
    "manifest_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to manifest YAML file",
)
@click.option(
    "--priority",
    type=click.Choice(["all", "critical", "high", "medium", "low"]),
    default="all",
    help="Only verify components of this priority or higher",
)
@pass_context
def verify(
    ctx: DxsContext,
    manifest_path: str,
    priority: str,
) -> None:
    """Verify analysis coverage against manifest.

    Checks which components in the manifest have analysis files
    and reports coverage statistics.

    \b
    Examples:
        dxs source explore verify --manifest outbound_manifest.yaml
        dxs source explore verify --manifest outbound_manifest.yaml --priority high
    """
    # Load manifest
    manifest_file = Path(manifest_path)
    with open(manifest_file, encoding="utf-8") as f:
        manifest_data = yaml.safe_load(f)

    base_dir = Path(manifest_data.get("base_dir", "."))
    components = manifest_data.get("components", [])

    # Priority filtering
    priority_levels = {"critical": 0, "high": 1, "medium": 2, "low": 3, "all": 99}
    min_priority = priority_levels.get(priority, 99)

    filtered = [
        c for c in components if priority_levels.get(c.get("priority", "low"), 3) <= min_priority
    ]

    # Re-check analysis status (may have changed since manifest generation)
    analyzed = []
    missing = []

    for comp in filtered:
        analysis_path = (
            base_dir
            / comp["library"]
            / str(comp["branch_id"])
            / comp["type"]
            / f"{comp['name']}.analysis.md"
        )

        if analysis_path.exists():
            analyzed.append(comp)
        else:
            missing.append(comp)

    # Group missing by priority
    missing_by_priority: dict[str, list[str]] = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
    }
    for comp in missing:
        p = comp.get("priority", "low")
        missing_by_priority[p].append(f"{comp['name']} ({comp['type']})")

    # Calculate coverage
    total = len(filtered)
    coverage_pct = (len(analyzed) / total * 100) if total > 0 else 0

    result = {
        "manifest": str(manifest_path),
        "filter_priority": priority,
        "total_checked": total,
        "analyzed": len(analyzed),
        "missing": len(missing),
        "coverage_percent": round(coverage_pct, 1),
        "missing_by_priority": {k: v for k, v in missing_by_priority.items() if v},
    }

    # Add list of missing if not too long
    if len(missing) <= 50:
        result["missing_components"] = [
            {"name": c["name"], "type": c["type"], "priority": c["priority"]} for c in missing
        ]

    ctx.output(single(item=result, semantic_key="verify"))


@explore.command("summarize")
@click.option(
    "--code-dir",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Directory containing .code.ts files",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output directory for summary files",
)
@pass_context
@restrict_in_restricted_mode("writes summary files to the filesystem")
def summarize(
    ctx: DxsContext,
    code_dir: str,
    output: str,
) -> None:
    """Generate summaries of extracted code files.

    NOTE: This command creates stub summary files that need to be
    filled in by an LLM agent. For automated summarization, use
    an external LLM tool to process the .code.ts files.

    \b
    Examples:
        dxs source explore summarize \\
          --code-dir ./exploration/Footprint/23403/code/ \\
          --output ./exploration/Footprint/23403/summaries/
    """
    code_path = Path(code_dir)
    out_path = Path(output)
    out_path.mkdir(parents=True, exist_ok=True)

    # Find all .code.ts files
    code_files = list(code_path.rglob("*.code.ts"))
    ctx.log(f"Found {len(code_files)} code files")

    summaries_created = 0

    for code_file in code_files:
        # Extract name from filename
        name = code_file.stem.replace(".code", "")

        # Get relative path for organization
        rel_path = code_file.relative_to(code_path)
        summary_dir = out_path / rel_path.parent
        summary_dir.mkdir(parents=True, exist_ok=True)

        summary_file = summary_dir / f"{name}.summary.yaml"

        # Read code to get line count
        with open(code_file, encoding="utf-8") as f:
            code_content = f.read()
        line_count = code_content.count("\n") + 1

        # Create stub summary
        stub = {
            "name": name,
            "source": str(rel_path),
            "lines": line_count,
            "purpose": "TODO: Describe what this flow does",
            "inputs": ["TODO: List input parameters"],
            "outputs": ["TODO: List output parameters"],
            "key_operations": ["TODO: List main operations"],
            "side_effects": {
                "creates": [],
                "updates": [],
                "deletes": [],
                "calls": [],
            },
            "business_rules": ["TODO: List business rules"],
            "complexity": "TODO: low/medium/high",
        }

        with open(summary_file, "w", encoding="utf-8") as f:
            yaml.dump(stub, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        summaries_created += 1

    ctx.output(
        single(
            item={
                "output_dir": str(out_path),
                "code_files_found": len(code_files),
                "summaries_created": summaries_created,
                "note": "Stub summaries created. Use an LLM agent to fill in the TODOs.",
            },
            semantic_key="summarize",
        )
    )
