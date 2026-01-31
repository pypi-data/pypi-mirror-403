import csv
from urllib.parse import urlparse

from .auth import load_auth_config, resolve_auth_config
from .manager import VaultManager

__all__ = ["create_parser", "main"]


def create_parser(parser):
    """Configures the parser for the 'sync' command."""
    parser.add_argument(
        "-s",
        "--source-vault-addr",
        required=True,
        help='Address of the source Vault (e.g., "http://127.0.0.1:8200")',
    )
    parser.add_argument(
        "-d",
        "--destination-vault-addr",
        required=True,
        help='Address of the destination Vault (e.g., "http://127.0.0.1:8200")',
    )
    parser.add_argument("-r", "--oidc-role", help="OIDC role for authentication")
    parser.add_argument(
        "--auth-config",
        help="Path to YAML auth config file (optional).",
    )
    parser.add_argument(
        "-o",
        "--override-secrets",
        help="Path to a CSV file with secrets to override during restore",
    )
    parser.add_argument(
        "--override-column",
        help="Name of the column in the override CSV to use for values. Defaults to the destination hostname.",
    )
    parser.add_argument(
        "--source-auth-method",
        help="Auth method for source Vault (default: oidc).",
    )
    parser.add_argument(
        "--source-auth-mount",
        help="Auth mount path for source Vault (kubernetes auth).",
    )
    parser.add_argument(
        "--source-auth-role",
        help="Auth role for source Vault (oidc/kubernetes).",
    )
    parser.add_argument(
        "--source-auth-jwt-path",
        help="JWT path for source Vault (kubernetes auth).",
    )
    parser.add_argument(
        "--dest-auth-method",
        help="Auth method for destination Vault (default: oidc).",
    )
    parser.add_argument(
        "--dest-auth-mount",
        help="Auth mount path for destination Vault (kubernetes auth).",
    )
    parser.add_argument(
        "--dest-auth-role",
        help="Auth role for destination Vault (oidc/kubernetes).",
    )
    parser.add_argument(
        "--dest-auth-jwt-path",
        help="JWT path for destination Vault (kubernetes auth).",
    )


def authenticate_vault(addr, auth_config, oidc_role):
    vault = VaultManager(addr)
    try:
        vault.authenticate(auth_config, oidc_role=oidc_role)
        print(f"Authenticated with Vault at {addr}")
        return vault
    except Exception as e:
        print(f"Failed to authenticate with Vault: {e}")
        return None


def confirm_destructive_action(dest_hostname, dest_addr):
    print("\n" + "=" * 80)
    print("!! WARNING: DESTRUCTIVE OPERATION !!")
    print(
        "You are about to restore a snapshot that will completely OVERWRITE all existing data"
    )
    print(f"in the destination Vault at: {dest_addr}")
    print("=" * 80)
    confirmation = input(
        f"To confirm this action, please type the destination hostname '{dest_hostname}': "
    )
    if confirmation != dest_hostname:
        print("Confirmation failed. Aborting synchronization.")
        return False
    return True


def take_and_restore_snapshot(source_vault, destination_vault):
    try:
        print("Taking snapshot from source Vault...")
        snapshot = source_vault.take_raft_snapshot()
        print("Snapshot taken.")
    except Exception as e:
        print(f"Failed to take snapshot: {e}")
        return None
    try:
        print("Restoring snapshot to destination Vault...")
        result = destination_vault.restore_raft_snapshot(snapshot)
        print("Snapshot restored.")
        return result
    except Exception as e:
        print(f"Failed to restore snapshot: {e}")
        return None


def apply_overrides_if_needed(
    result, args, destination_vault, dest_hostname, auth_config, oidc_role
):
    if result is None or result.status_code != 204 or args.override_secrets is None:
        return
    destination_vault.authenticate(auth_config, oidc_role=oidc_role)
    print(f"Applying overrides to destination Vault at {args.destination_vault_addr}")
    with open(args.override_secrets) as fin:
        reader = csv.reader(fin, dialect="excel-tab")
        headers = next(reader)
        header_map = {name.strip(): idx for idx, name in enumerate(headers)}
        override_column = (
            args.override_column if args.override_column else dest_hostname
        )
        required_headers = ["Secret", "Field", override_column]
        for col in required_headers:
            if col not in header_map:
                raise ValueError(f"Missing required column: {col}")
        idx_secret = header_map["Secret"]
        idx_field = header_map["Field"]
        idx_override = header_map[override_column]
        for row in reader:
            if (
                len(row) <= max(idx_secret, idx_field, idx_override)
                or not row[idx_secret]
                or not row[idx_field]
            ):
                continue
            secret_path = row[idx_secret].strip()
            field_key = row[idx_field].strip()
            override = row[idx_override].strip()
            try:
                secret = destination_vault.read_secret_path(secret_path)
                if secret is None:
                    print(
                        f"Warning: Cannot apply override for non-existent secret: {secret_path}"
                    )
                    continue
                secret[field_key] = override
                destination_vault.update_secret_path(secret_path, secret)
            except Exception as e:
                print(f"Error updating {secret_path}: {e}")
    print("Override apply complete.")


def main(args):
    config_data = load_auth_config(args.auth_config)
    source_auth = resolve_auth_config(
        cli_method=args.source_auth_method,
        cli_mount=args.source_auth_mount,
        cli_role=args.source_auth_role,
        cli_jwt_path=args.source_auth_jwt_path,
        env_prefix="VAULT_SRC",
        config_section=config_data.get("source"),
        oidc_role_fallback=args.oidc_role,
    )
    dest_auth = resolve_auth_config(
        cli_method=args.dest_auth_method,
        cli_mount=args.dest_auth_mount,
        cli_role=args.dest_auth_role,
        cli_jwt_path=args.dest_auth_jwt_path,
        env_prefix="VAULT_DST",
        config_section=config_data.get("destination"),
        oidc_role_fallback=args.oidc_role,
    )
    source_vault = authenticate_vault(
        args.source_vault_addr, source_auth, args.oidc_role
    )
    if not source_vault:
        return
    destination_vault = authenticate_vault(
        args.destination_vault_addr, dest_auth, args.oidc_role
    )
    if not destination_vault:
        return
    dest_hostname = urlparse(args.destination_vault_addr).hostname
    if not confirm_destructive_action(dest_hostname, args.destination_vault_addr):
        return
    result = take_and_restore_snapshot(source_vault, destination_vault)
    apply_overrides_if_needed(
        result, args, destination_vault, dest_hostname, dest_auth, args.oidc_role
    )
