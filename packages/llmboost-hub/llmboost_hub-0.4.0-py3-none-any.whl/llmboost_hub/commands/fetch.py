import click
import re
import requests
from typing import List, Dict
from llmboost_hub.commands.login import do_login
from llmboost_hub.utils.config import config
from llmboost_hub.utils import gpu_info
import tabulate
import pandas as pd
from llmboost_hub.utils.lookup_cache import load_lookup_df
from fnmatch import fnmatch


def matches_pattern(value: str, pattern: str) -> bool:
    """
    Check if a value matches a glob pattern (case-insensitive).
    Supports wildcards: * (any characters), ? (single character), [seq] (character set).

    Args:
        value: The string to test
        pattern: The glob pattern (e.g., '*llama*', 'AMD*', '*')

    Returns:
        True if value matches the pattern, False otherwise
    """
    return fnmatch(value.lower(), pattern.lower())


def do_fetch(
    query: str = r".*",
    verbose: bool = False,
    local_only: bool = False,
    skip_cache_update: bool = False,
    names_only: bool = False,
) -> pd.DataFrame:
    """
    Fetch remote/locally-cached lookup and filter by query and local GPU families.

    Supports wildcard patterns in both the lookup cache and query parameters:
        - Cache entries can use glob patterns (*, ?, [seq]) in model and gpu columns
        - User queries support the same glob patterns plus regex fallback
        - Examples: '*llama*', 'AMD*', 'meta-llama/*', '*'

    Behavior:
        - local_only=True: skip license check and network; load only from local cache file.
        - otherwise: attempt login/validation and fetch with cache fallback.
        - Bidirectional pattern matching: cache patterns match queries AND queries match cache entries.
        - Filter rows to those matching detected GPU families (supports GPU wildcards in cache).

    Args:
        query: Pattern to filter 'model' column (glob or regex, case-insensitive).
        verbose: If True, echo key steps.
        local_only: Skip license check and remote fetch; read from local cache only.
        skip_cache_update: Reserved for future use (cache policy is handled in loader).
        names_only: If True, return only the 'model' column.

    Returns:
        DataFrame with columns: model, gpu, docker_image (possibly empty).
    """
    if not local_only:
        # Best-effort: try to ensure license; even on failure, loader may still use cache
        do_login(license_file=None, verbose=verbose)
    lookup_df = load_lookup_df(
        config.LBH_LOOKUP_URL,
        query,
        verbose=verbose,
        local_only=local_only,
        skip_cache_update=skip_cache_update,
    )

    # Filter by query (supports wildcards in cache and bidirectional matching)
    # Match if: (1) cache model pattern matches user query, OR (2) user query pattern matches cache model
    def model_matches_query(model_str: str) -> bool:
        model_str = str(model_str)
        # Check if cache entry pattern (which may contain wildcards) matches user query
        if matches_pattern(query, model_str):
            return True
        # Check if user query pattern (which may contain wildcards) matches cache entry
        if matches_pattern(model_str, query):
            return True
        # Fallback to regex for backward compatibility
        if re.search(query, model_str, flags=re.IGNORECASE):
            return True
        return False

    filtered_df = lookup_df[lookup_df["model"].apply(model_matches_query)].reset_index(drop=True)
    filtered_df.index += 1  # user-friendly display index

    # GPU family filter (supports wildcards in cache GPU patterns)
    available_gpus = gpu_info.get_gpus()
    local_families = {gpu_info.gpu_name2family(g) for g in available_gpus if g}

    def gpu_matches_local(gpu_str: str) -> bool:
        """Check if cache GPU pattern matches any local GPU family."""
        gpu_str = str(gpu_str)
        gpu_family = gpu_info.gpu_name2family(gpu_str)

        # Check exact family match first
        if gpu_family in local_families:
            return True

        # Check if cache GPU pattern (which may contain wildcards) matches any local GPU family
        for local_fam in local_families:
            if matches_pattern(local_fam, gpu_str) or matches_pattern(local_fam, gpu_family):
                return True
            # Also check full GPU string for wildcard match
            for local_gpu in available_gpus:
                if matches_pattern(local_gpu, gpu_str):
                    return True

        return False

    filtered_df = filtered_df[filtered_df["gpu"].apply(gpu_matches_local)].reset_index(drop=True)
    filtered_df.index += 1  # user-friendly display index

    # Short-circuit: names only
    if names_only:
        return filtered_df[["model"]]

    return filtered_df


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("query", type=str, default=r".*", required=False)
@click.option(
    "--local-only",
    is_flag=True,
    help="Use only the local lookup cache (skip online fetch and license validation).",
)
@click.option(
    "--skip-cache-update",
    is_flag=True,
    help="Fetch, but skip updating local cache. (not applicable with --local-only).",
)
@click.option(
    "--names-only",
    is_flag=True,
    help="Return model names only.",
)
@click.pass_context
def fetch(ctx: click.Context, query, local_only, skip_cache_update, names_only):
    """
    Fetch for models in the LLMBoost registry.
    """
    verbose = ctx.obj.get("VERBOSE", False)
    results_df = do_fetch(
        query,
        verbose=verbose,
        local_only=local_only,
        skip_cache_update=skip_cache_update,
        names_only=names_only,
    )

    click.echo(f"Found {len(results_df)} relevant images")
    if results_df.empty:
        return

    # Present results via tabulate
    click.echo(
        tabulate.tabulate(
            results_df.values.tolist(),
            headers=list(results_df.columns),
            showindex=list(results_df.index),
            tablefmt="psql",
        )
    )
    return results_df
