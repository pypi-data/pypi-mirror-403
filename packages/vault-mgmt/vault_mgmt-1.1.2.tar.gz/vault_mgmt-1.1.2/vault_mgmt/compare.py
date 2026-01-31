import csv
import os
import sys
from urllib.parse import urlparse

from tqdm import tqdm

from .auth import load_auth_config, resolve_auth_config
from .manager import VaultManager

__all__ = ["create_parser", "main"]


def create_parser(parser):
    """Configures the parser for the 'compare' command."""
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    default_output = f"{script_name}_results.csv"

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
        "-b",
        "--base-path",
        default="",
        help="Base path within the mount to compare (default: root).",
    )
    parser.add_argument(
        "--mount-point",
        default="secret",
        help="Secret mount point to compare (default: secret).",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        default=default_output,
        help=f"Path to tab-delimited CSV output file (default: {default_output})",
    )
    parser.add_argument(
        "--ignore-path",
        action="append",
        default=[],
        help="Path to ignore during comparison. Can be specified multiple times.",
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


def authenticate_vault(addr, auth_config=None, oidc_role=None):
    if auth_config is None:
        auth_config = resolve_auth_config(
            cli_method=None,
            cli_mount=None,
            cli_role=None,
            cli_jwt_path=None,
            env_prefix=None,
            config_section=None,
            oidc_role_fallback=oidc_role,
        )
    vault = VaultManager(addr)
    try:
        vault.authenticate(auth_config, oidc_role=oidc_role)
        print(f"Authenticated with Vault at {addr}")
        return vault
    except Exception as e:
        print(f"Failed to authenticate with Vault: {e}")
        return None


def get_filtered_secret_paths(vault, base_path, ignore_paths, mount_point="secret"):
    paths = set(
        vault.list_all_secret_paths(base_path=base_path, mount_point=mount_point)
    )
    for ignore in ignore_paths:
        paths = {p for p in paths if ignore not in p}
    return paths

def compare_secrets(source_vault, dest_vault, common_paths):
    """
    Compare secrets at specified paths between two VaultManager instances.

    For each path in `paths`, this function compares the key-value pairs in the source and destination Vaults.
    If a key exists in the source but is missing or has a different value in the destination, a row is added to the result.

    Args:
        source_vault (VaultManager): The source Vault client.
        dstdest_vault (VaultManager): The destination Vault client.
        common_paths (Iterable[str]): Iterable of secret paths to compare. Only paths present in the source are compared.

    Returns:
        List[List]: A list of lists, where each inner list represents a difference and contains:
            - secret_path (str): The secret path.
            - field (str): The key within the secret.
            - source_value (Any): The value from the source Vault (may be None).
            - dest_value (Any): The value from the destination Vault (may be None).

    Example:
        [
            ["foo/bar", "password", "s3cr3t", None],           # Key missing in destination
            ["foo/bar", "username", "admin", "user"],          # Value differs
        ]

    Notes:
        - Only paths present in the source are compared.
        - If a path is missing in the destination, all keys from the source are reported with dest_value as None.
        - If a key is missing in the destination, dest_value is None.
        - If a key's value differs, both source_value and dest_value are shown.
        - No output is produced for keys that are identical in both Vaults.
        - Prints an error message to stdout if comparison of a path fails.
    """
    results = []
    for secret_path in tqdm(common_paths, desc="Comparing secrets"):
        try:
            source_secret = source_vault.read_secret_path(secret_path)
            destination_secret = dest_vault.read_secret_path(secret_path)
            if source_secret != destination_secret:
                source_secret = source_secret or {}
                destination_secret = destination_secret or {}
                all_keys = set(source_secret.keys()) | set(destination_secret.keys())
                for field in all_keys:
                    source_field = source_secret.get(field)
                    destination_field = destination_secret.get(field)
                    if source_field != destination_field:
                        results.append(
                            [secret_path, field, source_field, destination_field]
                        )
        except Exception as e:
            print(f"Failed to compare secret at path '{secret_path}': {e}")
    return results


def write_results_to_csv(results, args):
    if results:
        with open(args.output_file, mode="w", newline="") as fout:
            writer = csv.writer(fout, dialect="excel-tab")
            writer.writerow(
                [
                    "Secret",
                    "Field",
                    f"{urlparse(args.source_vault_addr).hostname}",
                    f"{urlparse(args.destination_vault_addr).hostname}",
                ]
            )
            writer.writerows(results)
        print(
            f"\nCompare complete. Found {len(results)} differences. Results saved to {args.output_file}"
        )
    else:
        print("\nCompare complete. No differences found. No output file written.")


def main(args):
    """Main logic for comparing secrets."""
    mount_point = args.mount_point.strip("/") if args.mount_point else "secret"
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
    print(
        f"Listing secret paths from source Vault at mount '{mount_point}' and base path '{args.base_path}/'..."
    )
    source_secret_paths = get_filtered_secret_paths(
        source_vault, args.base_path, args.ignore_path, mount_point
    )
    print(f"Found {len(source_secret_paths)} secret paths in source.")
    print(
        f"Listing secret paths from destination Vault at mount '{mount_point}' and base path '{args.base_path}/'..."
    )
    destination_secret_paths = get_filtered_secret_paths(
        destination_vault, args.base_path, args.ignore_path, mount_point
    )
    print(f"Found {len(destination_secret_paths)} secret paths in destination.")
    common_paths = source_secret_paths & destination_secret_paths
    print(f"Found {len(common_paths)} common secrets to compare...")
    results = compare_secrets(source_vault, destination_vault, common_paths)
    write_results_to_csv(results, args)
