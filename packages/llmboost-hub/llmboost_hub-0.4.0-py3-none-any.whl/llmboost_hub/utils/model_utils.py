import os
import yaml
from typing import List, Optional, Dict
from pathlib import Path
from llmboost_hub.utils.config import config


def load_model_paths() -> Dict[str, str]:
    """
    Load model-to-path mappings from config.LBH_MODEL_PATHS.

    Returns:
        Dictionary mapping full model names (repo/model_name) to their paths.
        Empty dict if file doesn't exist or is malformed.
    """

    yaml_path = config.LBH_MODEL_PATHS
    if not os.path.exists(yaml_path):
        return {}

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        # Support nested 'model_paths' key for the specified format
        if "model_paths" in data:
            return data["model_paths"] or {}
        return data


def save_model_paths(mappings: Dict[str, str]) -> None:
    """
    Save model-to-path mappings to config.LBH_MODEL_PATHS.

    Args:
        mappings: Dictionary mapping full model names (repo/model_name) to their paths.
    """

    yaml_path = config.LBH_MODEL_PATHS
    os.makedirs(os.path.dirname(yaml_path), exist_ok=True)

    data = {"model_paths": mappings}

    with open(yaml_path, "w", encoding="utf-8") as f:
        return yaml.safe_dump(data, f, sort_keys=True, default_flow_style=False)


def get_model_path(model: str) -> Optional[str]:
    """
    Get the stored path for a model from the mapping file.

    Args:
        model: Full model identifier (repo/model_name format).

    Returns:
        The stored path if found and it exists on disk; otherwise None.
    """
    mappings = load_model_paths()
    path = mappings.get(model)

    # Return path only if it exists on disk
    if path and os.path.exists(path):
        return path

    return None


def set_model_path(model: str, path: str) -> None:
    """
    Store or update a model's path in the mapping file.

    Args:
        model: Full model identifier (repo/model_name format).
        path: Absolute path to the model directory on the host.
    """
    mappings = load_model_paths()
    mappings[model] = path
    save_model_paths(mappings)


def path_has_files(path: str) -> bool:
    """
    Return True if 'path' exists, is a directory, and contains at least one file
    in its subtree (current dir or any nested subdirectory).

    Args:
        path: Absolute or relative directory path.

    Returns:
        True if there is at least one regular file somewhere under 'path'; False otherwise.
    """
    # Fast-fail if not a directory
    if not os.path.isdir(path):
        return False
    # Walk the tree and short-circuit as soon as we see any file
    for _, _, files in os.walk(path):
        if files:
            return True
    return False


def is_model_downloaded(models_root: str, model_id: str) -> bool:
    """
    Check if the models root contains a downloaded model directory for `model_id`.

    Args:
        models_root: Root directory that stores models (e.g., `config.LBH_MODELS`).
        model_id: Model identifier; may include `org/name` or plain name.

    Returns:
        True if `models_root/model_id` exists and contains at least one file; False otherwise.
    """
    return path_has_files(os.path.join(models_root, str(model_id or "")))


def get_model_name_from_model_id(model_id: str) -> str:
    """
    Get name of model from a Hugging Face style model id.
    Applies following transformations:
        - Remove repo/organization prefix (if present; splits on '/')
    Converts any 'org/name' to just 'name'.

    Examples:
        'Org/Model_Name' -> 'Model_name'
        'model.name'     -> 'model.name'

    Args:
        model_id: Model id such as 'org/name' or 'name'.

    Returns:
        Normalized model name.
    """
    parts = str(model_id or "").split("/")
    return parts[-1]  # get last part after '/'


def get_repo_from_model_id(model_id: str) -> str:
    """
    Extract the organization/user (repo owner) from a Hugging Face style model id.

    Examples:
        'org/name' -> 'org'
        'name'     -> ''  (no org present)

    Args:
        model_id: Model id such as 'org/name' or 'name'.

    Returns:
        The repo/organization segment if present; otherwise an empty string.
    """
    parts = str(model_id or "").split("/")
    return parts[-2] if len(parts) >= 2 else ""


def get_downloaded_models_matching_pattern(pattern: str = "*") -> List[str]:
    """
    Get list of downloaded models that match a glob pattern.
    Checks both LBH_MODEL_PATHS and the models directory.

    Args:
        pattern: Glob pattern to match models (default: '*' for all models)

    Returns:
        List of model identifiers that match the pattern and are downloaded.
    """
    from fnmatch import fnmatch

    downloaded = []

    # Get models from model_paths.yaml
    model_paths = load_model_paths()
    for model_id, path in model_paths.items():
        if fnmatch(model_id.lower(), pattern.lower()) and os.path.exists(path):
            downloaded.append(model_id)

    # Also scan the models directory for any models not in model_paths
    models_dir = config.LBH_MODELS
    if os.path.isdir(models_dir):
        staging_dir_basename = os.path.basename(config.LBH_MODELS_STAGING)
        for repo in os.listdir(models_dir):
            repo_path = os.path.join(models_dir, repo)
            if not os.path.isdir(repo_path) or repo == staging_dir_basename:
                continue

            for model_name in os.listdir(repo_path):
                model_path = os.path.join(repo_path, model_name)
                if not os.path.isdir(model_path):
                    continue

                full_model_id = f"{repo}/{model_name}"
                if fnmatch(full_model_id.lower(), pattern.lower()):
                    if full_model_id not in downloaded and path_has_files(model_path):
                        downloaded.append(full_model_id)

    return sorted(set(downloaded))
