import textwrap

from vault_mgmt.auth import (
    DEFAULT_K8S_JWT_PATH,
    load_auth_config,
    resolve_auth_config,
)


def test_load_auth_config_yaml(tmp_path):
    config_path = tmp_path / "auth.yml"
    config_path.write_text(
        textwrap.dedent(
            """
            source:
              method: kubernetes
              mount: k8s-a
              role: read
            destination:
              method: kubernetes
              mount: k8s-b
              role: write
            """
        ).lstrip()
    )
    data = load_auth_config(str(config_path))
    assert data["source"]["mount"] == "k8s-a"
    assert data["destination"]["role"] == "write"


def test_resolve_auth_config_defaults_to_oidc_role():
    auth = resolve_auth_config(
        cli_method=None,
        cli_mount=None,
        cli_role=None,
        cli_jwt_path=None,
        env_prefix=None,
        config_section=None,
        oidc_role_fallback="oidc-role",
    )
    assert auth.method == "oidc"
    assert auth.role == "oidc-role"


def test_resolve_auth_config_kubernetes_defaults():
    auth = resolve_auth_config(
        cli_method="kubernetes",
        cli_mount=None,
        cli_role="k8s-role",
        cli_jwt_path=None,
        env_prefix=None,
        config_section=None,
        oidc_role_fallback=None,
    )
    assert auth.method == "kubernetes"
    assert auth.mount == "kubernetes"
    assert auth.role == "k8s-role"
    assert auth.jwt_path == DEFAULT_K8S_JWT_PATH


def test_resolve_auth_config_cli_overrides_env_and_config(monkeypatch):
    monkeypatch.setenv("VAULT_SRC_AUTH_METHOD", "kubernetes")
    monkeypatch.setenv("VAULT_SRC_AUTH_ROLE", "env-role")
    config_section = {"method": "oidc", "role": "config-role", "mount": "config"}
    auth = resolve_auth_config(
        cli_method=None,
        cli_mount=None,
        cli_role="cli-role",
        cli_jwt_path=None,
        env_prefix="VAULT_SRC",
        config_section=config_section,
        oidc_role_fallback=None,
    )
    assert auth.method == "kubernetes"
    assert auth.role == "cli-role"
