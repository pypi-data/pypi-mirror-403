import click
import subprocess
from typing import List
import re
import pandas as pd
import tabulate

from llmboost_hub.commands.fetch import do_fetch, matches_pattern
from llmboost_hub.utils.config import config
from llmboost_hub.utils import gpu_info
from llmboost_hub.utils.container_utils import (
    container_name_for_model,
    is_container_running,
    is_model_initializing,
    is_model_ready2serve,
    is_model_tuning,
)
from llmboost_hub.utils.model_utils import is_model_downloaded, load_model_paths
import os


def _get_local_images() -> List[str]:
    """
    Return a list of local docker images in the format 'repository:tag'.

    Notes:
        Best-effort; falls back to an empty list on errors.
    """
    try:
        out = subprocess.check_output(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"], text=True
        )
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        return lines
    except Exception:
        return []


def _get_installed_models(models_dir: str) -> List[str]:
    """
    Return list of installed model names (normalized).
    Equivalent to `grep -LrE '^  "(_name_or_path|architectures)": ' "{config.LBH_MODELS}/**/*.json" | xargs dirname | sort | uniq`.

    Staging dir (config.LBH_MODELS_STAGING) is ignored.
    """
    models: List[str] = []
    try:
        staging_dir_basename = os.path.basename(config.LBH_MODELS_STAGING)

        for repo in os.listdir(models_dir):
            repo_path = os.path.join(models_dir, repo)
            if not os.path.isdir(repo_path):
                continue
            # skip staging directory entirely
            if repo == staging_dir_basename:
                continue

            # collect second-level model directories under each repo
            subdirs = [
                d for d in os.listdir(repo_path) if os.path.isdir(os.path.join(repo_path, d))
            ]
            if subdirs:
                models.extend(subdirs)
            else:
                # fallback: treat top-level dir as model (legacy layouts)
                models.append(repo)
    except Exception:
        pass
    # deduplicate while preserving order
    seen = set()
    uniq_models = []
    for m in models:
        if m not in seen:
            seen.add(m)
            uniq_models.append(m)
    return uniq_models


def _resolve_model_path(models_root: str, model_name: str) -> str:
    """
    Best-effort: resolve absolute path for a model_name under LBH_MODELS by scanning
    <repo>/<model> while ignoring the staging dir. Falls back to <models_root>/<model_name>.
    """
    try:
        staging_dir = getattr(config, "LBH_MODELS_STAGING", None)
        staging_dir = os.path.abspath(staging_dir) if staging_dir else None

        for repo in os.listdir(models_root):
            repo_path = os.path.join(models_root, repo)
            if not os.path.isdir(repo_path):
                continue
            # skip staging directory
            if staging_dir and os.path.abspath(repo_path) == staging_dir:
                continue

            candidate = os.path.join(repo_path, model_name)
            if os.path.isdir(candidate):
                return candidate
    except Exception:
        pass
    # fallback
    return os.path.join(models_root, model_name)


def do_list(query: str = r".*", local_only: bool = True, verbose: bool = False) -> dict:
    """
    List models from model_paths.yaml with their status and GPU compatibility.
    Only shows models that have been prepared via `lbh prep`.

    Args:
        query: Optional LIKE filter for narrowing models.
        local_only: If True, fetch only uses local cache (no network).
        verbose: If True, emit warnings about ambiguous GPUs.

    Returns:
        Dict:
            - images: List[str] unique docker images referenced
            - installed_models: List[str] from model_paths.yaml
            - gpus: List[str] detected GPU names
            - images_df: pd.DataFrame of models with status
            - lookup_df: pd.DataFrame of filtered lookup rows
    """
    # Load models from model_paths.yaml (source of truth)
    model_paths = load_model_paths()

    # Load lookup cache for metadata
    cache_df = pd.DataFrame()
    try:
        cache_df = do_fetch(query=query, verbose=verbose, local_only=local_only)
        # Normalize column names
        cache_df.columns = [str(c).strip().lower() for c in cache_df.columns]
    except Exception:
        cache_df = pd.DataFrame(columns=["model", "gpu", "docker_image"])

    # Build dataframe from model_paths.yaml with metadata from cache
    merged_rows = []
    for model_id, model_path in model_paths.items():
        # Filter by query if provided
        if query and query != r".*":
            if not re.search(query, model_id, re.IGNORECASE):
                continue

        # Find matching cache entry (supports wildcard patterns in cache)
        from llmboost_hub.utils.lookup_cache import find_cache_entry_for_model

        cache_entry = find_cache_entry_for_model(model_id, verbose=False)

        if cache_entry is not None:
            # Use cache metadata
            row = {
                "model": model_id,
                "gpu": str(cache_entry.get("gpu", "")),
                "docker_image": str(cache_entry.get("docker_image", "")),
                "path": model_path,
            }
        else:
            # No cache entry found, use defaults
            row = {
                "model": model_id,
                "gpu": "",
                "docker_image": "",
                "path": model_path,
            }
        merged_rows.append(row)

    merged_df = (
        pd.DataFrame(merged_rows)
        if merged_rows
        else pd.DataFrame(columns=["model", "gpu", "docker_image", "path"])
    )

    # Add GPU match indicator column based on local GPU families (supports wildcards)
    local_gpus = gpu_info.get_gpus()
    local_families = {gpu_info.gpu_name2family(g) for g in local_gpus if g}
    if not merged_df.empty:

        def gpu_matches_local(gpu_str: str) -> bool:
            """Check if cache GPU pattern (including wildcards) matches any local GPU."""
            gpu_str = str(gpu_str)
            gpu_family = gpu_info.gpu_name2family(gpu_str)

            # Check exact family match first
            if gpu_family in local_families:
                return True

            # Check wildcard patterns
            for local_fam in local_families:
                if matches_pattern(local_fam, gpu_str) or matches_pattern(local_fam, gpu_family):
                    return True
                for local_gpu in local_gpus:
                    if matches_pattern(local_gpu, gpu_str):
                        return True

            return False

        merged_df = merged_df.assign(matches_local_gpu=merged_df["gpu"].apply(gpu_matches_local))

    # Derive status column based on path existence and container/process state
    if not merged_df.empty:
        statuses: List[str] = []
        for _, row in merged_df.iterrows():
            model_id = str(row.get("model", "") or "")
            model_path = str(row.get("path", "") or "")

            # Check if path exists (primary check)
            from llmboost_hub.utils.model_utils import path_has_files

            if not model_path or not path_has_files(model_path):
                statuses.append("pending")
                continue

            # Path exists, check container state
            cname = container_name_for_model(model_id) if model_id else ""
            if cname and is_container_running(cname):
                # Priority: tuning > serving > initializing > running
                if is_model_tuning(cname):
                    statuses.append("tuning")
                elif is_model_ready2serve(cname):
                    statuses.append("serving")
                elif is_model_initializing(cname):
                    statuses.append("initializing")
                else:
                    statuses.append("running")
            else:
                statuses.append("stopped")
        merged_df = merged_df.assign(status=statuses)

    # Extract unique docker images from merged data
    images = (
        sorted(set(merged_df["docker_image"].dropna().astype(str).tolist()))
        if not merged_df.empty
        else []
    )

    # GPUs via utility (standardized)
    gpus: List[str] = gpu_info.get_gpus()

    # Optional note about multiple GPUs (can affect matching)
    if len(set(gpus)) > 1 and verbose:
        click.echo("Warning: Multiple GPUs detected.")

    return {
        "images": images,
        "installed_models": list(model_paths.keys()),
        "gpus": gpus,
        "images_df": merged_df,
        "lookup_df": cache_df,
    }


def _is_model_directory(path: str) -> bool:
    """
    Check if a directory looks like a Hugging Face model directory.

    Args:
        path: Directory path to check.

    Returns:
        True if directory contains model files (config.json, tokenizer files, etc.)
    """
    if not os.path.isdir(path):
        return False

    # Look for common model files
    model_indicators = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "pytorch_model.bin",
        "model.safetensors",
    ]

    for indicator in model_indicators:
        if os.path.exists(os.path.join(path, indicator)):
            return True

    # Check for safetensors files with patterns
    try:
        files = os.listdir(path)
        for f in files:
            if f.endswith(".safetensors") or f.endswith(".bin"):
                return True
    except (PermissionError, OSError):
        pass

    return False


def _discover_models(discover_path: str, verbose: bool = False) -> None:
    """
    Discover models in a directory and prompt user to add them to model_paths.yaml.

    Args:
        discover_path: Absolute path to directory to scan for models.
        verbose: If True, show additional details.
    """
    from llmboost_hub.utils.model_utils import path_has_files, save_model_paths
    from llmboost_hub.utils.lookup_cache import find_cache_entry_for_model

    click.echo(f"Scanning {discover_path} for models...")

    # Scan for model directories
    discovered = []

    # Try to find models in org/model structure
    try:
        for entry in os.listdir(discover_path):
            entry_path = os.path.join(discover_path, entry)
            if not os.path.isdir(entry_path):
                continue

            # Skip staging directory
            if entry == os.path.basename(config.LBH_MODELS_STAGING):
                continue

            # Check if this is a model directory directly
            if _is_model_directory(entry_path):
                # Could be a model directory (e.g., "Llama-3.1-8B-Instruct")
                discovered.append(
                    {
                        "path": entry_path,
                        "inferred_id": entry,  # Just the name, no org
                    }
                )

            # Check subdirectories (org/model structure)
            try:
                for subentry in os.listdir(entry_path):
                    subentry_path = os.path.join(entry_path, subentry)
                    if _is_model_directory(subentry_path):
                        # Org/model structure
                        discovered.append(
                            {
                                "path": subentry_path,
                                "inferred_id": f"{entry}/{subentry}",
                            }
                        )
            except (PermissionError, OSError):
                # Skip directories we can't read
                if verbose:
                    click.echo(f"Warning: Cannot read {entry_path} (permission denied)")
                continue
    except Exception as e:
        click.echo(f"Error scanning directory: {e}")
        return

    if not discovered:
        click.echo(f"No model directories found in {discover_path}")
        return

    # Build table with cache metadata
    rows = []
    for item in discovered:
        model_id = item["inferred_id"]
        model_path = item["path"]

        # Try to find cache entry
        cache_entry = find_cache_entry_for_model(model_id, verbose=False)

        if cache_entry is not None:
            gpu = str(cache_entry.get("gpu", "unknown"))
            docker_image = str(cache_entry.get("docker_image", "unknown"))
        else:
            gpu = "unknown"
            docker_image = "unknown"

        rows.append(
            {
                "model": model_id,
                "path": model_path,
                "gpu": gpu,
                "docker_image": docker_image,
            }
        )

    # Show discovered models
    df = pd.DataFrame(rows)
    df.index += 1

    click.echo(f"\\nFound {len(df)} model(s):\\n")
    click.echo(
        tabulate.tabulate(
            df.values.tolist(),
            headers=list(df.columns),
            showindex=list(df.index),
            tablefmt="psql",
        )
    )

    # Prompt to add to model_paths.yaml
    if not click.confirm("\\nAdd these models to model_paths.yaml?", default=True):
        click.echo("Cancelled.")
        return

    # Load existing model paths and merge
    from llmboost_hub.utils.model_utils import load_model_paths

    existing_paths = load_model_paths()

    added = 0
    updated = 0
    for row in rows:
        model_id = row["model"]
        model_path = row["path"]

        if model_id in existing_paths:
            if existing_paths[model_id] != model_path:
                click.echo(f"Updating {model_id}: {existing_paths[model_id]} -> {model_path}")
                existing_paths[model_id] = model_path
                updated += 1
            else:
                click.echo(f"Skipping {model_id} (already present with same path)")
        else:
            click.echo(f"Adding {model_id}: {model_path}")
            existing_paths[model_id] = model_path
            added += 1

    # Save updated model paths
    save_model_paths(existing_paths)
    click.echo(f"\\nDone! Added {added} model(s), updated {updated} model(s).")


@click.command(name="list", context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("query", required=False, default="")
@click.option(
    "--discover",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=None,
    help=f"Discover models in the specified directory and prompt to add them to {config.LBH_MODEL_PATHS}",
)
@click.pass_context
def list_models(ctx: click.Context, query, discover):
    f"""
    List models from {config.LBH_MODEL_PATHS} with their status and GPU compatibility.
    Shows models that have been prepared via `lbh prep` or discovered via `--discover`.
    These models are tracked in {config.LBH_MODEL_PATHS}.

    \b
    Discovery mode (--discover /path):
        Scans the specified directory for model subdirectories.
        Shows a table of discovered models.
        Prompts to add selected models to {config.LBH_MODEL_PATHS}.

    \b
    Statuses:
        - pending: Model path doesn't exist or is empty.
        - stopped: Model exists but container not running.
        - initializing: Container starting up (model loading in progress).
        - running: Container running but not serving requests.
        - serving: Container running and ready to serve requests.
        - tuning: Container running and performing model tuning.
    """
    verbose = ctx.obj.get("VERBOSE", False)

    # Discovery mode: scan directory for models
    if discover:
        _discover_models(discover, verbose)
        return

    # Default mode: list models from model_paths.yaml
    data = do_list(query=query, verbose=verbose)
    images_df = data.get("images_df")

    # Get DataFrame of supported models
    df = images_df if isinstance(images_df, pd.DataFrame) else pd.DataFrame()

    click.echo(f"Found {len(df)} supported models")

    # Ensure desired column ordering if available
    desired_cols = [c for c in ["status", "model", "gpu", "docker_image"] if c in df.columns]
    if desired_cols:
        df = df[desired_cols]
    df.index += 1  # start index at 1

    click.echo(
        tabulate.tabulate(
            df.values.tolist(),
            headers=list(df.columns),
            showindex=list(df.index),
            tablefmt="psql",
        )
    )

    # Extra details in verbose mode
    if not verbose:
        return

    # Tabulate model paths from model_paths.yaml
    click.echo(f"\nModel paths (from {config.LBH_MODEL_PATHS}):")
    if data["installed_models"]:
        model_paths = load_model_paths()
        if model_paths:
            models_df = pd.DataFrame(
                [
                    {"model": model_id, "path": path}
                    for model_id, path in sorted(model_paths.items())
                ]
            )
            models_df.index += 1
            click.echo(
                tabulate.tabulate(
                    models_df.values.tolist(),
                    headers=list(models_df.columns),
                    showindex=list(models_df.index),
                    tablefmt="psql",
                )
            )
        else:
            click.echo(" (no models in model_paths.yaml)")
    else:
        click.echo(" (no models in model_paths.yaml)")

    click.echo("\nDetected GPUs (best-effort):")
    if data["gpus"]:
        for g in set(data["gpus"]):
            click.echo(f" - {g} ({gpu_info.gpu_name2family(g)})")
    else:
        click.echo(" (unable to detect GPUs)")
