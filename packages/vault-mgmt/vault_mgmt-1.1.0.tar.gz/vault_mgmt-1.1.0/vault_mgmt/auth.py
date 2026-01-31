import os
from dataclasses import dataclass
from typing import Any, Optional

import yaml

DEFAULT_K8S_JWT_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"


@dataclass(frozen=True)
class AuthConfig:
    method: str
    mount: Optional[str]
    role: Optional[str]
    jwt_path: Optional[str]


def load_auth_config(path: Optional[str]) -> dict[str, Any]:
    if not path:
        return {}
    try:
        with open(path) as fin:
            data = yaml.safe_load(fin)
    except FileNotFoundError as exc:
        raise ValueError(f"Auth config file not found at: {path}") from exc
    if not data:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Auth config must be a mapping at the top level.")
    return data


def _read_env(prefix: str, key: str) -> Optional[str]:
    return os.getenv(f"{prefix}_{key}")


def resolve_auth_config(
    *,
    cli_method: Optional[str],
    cli_mount: Optional[str],
    cli_role: Optional[str],
    cli_jwt_path: Optional[str],
    env_prefix: Optional[str],
    config_section: Optional[dict[str, Any]],
    oidc_role_fallback: Optional[str],
    default_method: str = "oidc",
) -> AuthConfig:
    section = config_section or {}

    env_method = _read_env(env_prefix, "AUTH_METHOD") if env_prefix else None
    env_mount = _read_env(env_prefix, "AUTH_MOUNT") if env_prefix else None
    env_role = _read_env(env_prefix, "AUTH_ROLE") if env_prefix else None
    env_jwt_path = _read_env(env_prefix, "AUTH_JWT_PATH") if env_prefix else None

    method = (
        cli_method
        or env_method
        or section.get("method")
        or default_method
    )
    method = method.lower()

    mount = cli_mount or env_mount or section.get("mount")
    role = cli_role or env_role or section.get("role")
    jwt_path = cli_jwt_path or env_jwt_path or section.get("jwt_path")

    if method == "oidc" and not role:
        role = oidc_role_fallback

    if method == "kubernetes":
        if not mount:
            mount = "kubernetes"
        if not jwt_path:
            jwt_path = DEFAULT_K8S_JWT_PATH

    return AuthConfig(method=method, mount=mount, role=role, jwt_path=jwt_path)
