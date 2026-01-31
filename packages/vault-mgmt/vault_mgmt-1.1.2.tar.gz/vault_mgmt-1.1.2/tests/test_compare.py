import argparse
from unittest.mock import MagicMock, patch

from vault_mgmt import compare


class FakeVaultManager:
    def __init__(self, secrets):
        self.secrets = secrets


    def read_secret_path(self, path):
        return self.secrets.get(path)
    

def test_create_parser():
    parser = argparse.ArgumentParser()
    compare.create_parser(parser)
    assert isinstance(parser, argparse.ArgumentParser)


def test_main_help(capsys):
    parser = argparse.ArgumentParser()
    compare.create_parser(parser)
    # Simulate --help, which should exit with code 0
    try:
        parser.parse_args(['--help'])
    except SystemExit as e:
        assert e.code == 0


def test_main_minimal(monkeypatch):
    parser = argparse.ArgumentParser()
    compare.create_parser(parser)
    # Provide minimal required args (will fail to connect, but should not crash)
    args = parser.parse_args([
        '-s', 'http://localhost:8200',
        '-d', 'http://localhost:8201'
    ])
    compare.main(args)  # Should print auth failure, not crash


def test_authenticate_vault_print_and_return(capfd):
    addr = "https://vault.example.com"
    oidc_role = "test-role"
    # Patch VaultManager so no real connection is made
    with patch("vault_mgmt.compare.VaultManager") as MockVaultManager:
        mock_vault = MagicMock()
        MockVaultManager.return_value = mock_vault
        # Patch the authenticate_with_oidc method
        mock_vault.authenticate_with_oidc.return_value = None

        # Act
        result = compare.authenticate_vault(addr, oidc_role)
        out, _ = capfd.readouterr()

        # Assert
        assert f"Authenticated with Vault at {addr}\n" in out
        assert result is mock_vault


def test_get_filtered_secret_paths_no_ignores():
    vault = MagicMock()
    vault.list_all_secret_paths.return_value = [
        "base/foo", "base/bar/baz", "base/test"
    ]
    base_path = "base/"
    ignore_paths = []
    result = compare.get_filtered_secret_paths(vault, base_path, ignore_paths)
    assert result == {"base/foo", "base/bar/baz", "base/test"}


def test_get_filtered_secret_paths_with_ignores():
    vault = MagicMock()
    vault.list_all_secret_paths.return_value = [
        "base/foo", "base/bar/baz", "base/test"
    ]
    base_path = "base/"
    ignore_paths = ["foo", "baz"]
    result = compare.get_filtered_secret_paths(vault, base_path, ignore_paths)
    assert result == {"base/test"}


def test_get_filtered_secret_paths_all_ignored():
    vault = MagicMock()
    vault.list_all_secret_paths.return_value = [
        "base/foo", "base/bar/baz"
    ]
    base_path = "base/"
    ignore_paths = ["foo", "baz", "bar"]
    result = compare.get_filtered_secret_paths(vault, base_path, ignore_paths)
    assert result == set()


def test_compare_secrets_identical():
    secrets = {
        "foo/bar": {"key": "value"},
        "baz/qux": {"another": "thing"},
    }
    src = FakeVaultManager(secrets)
    dst = FakeVaultManager(secrets.copy())
    paths = ["foo/bar", "baz/qux"]
    result = compare.compare_secrets(src, dst, paths)
    assert result == []


def test_compare_secrets_difference():
    src = FakeVaultManager({"foo/bar": {"key": "value"}})
    dst = FakeVaultManager({"foo/bar": {"key": "DIFFERENT"}})
    paths = ["foo/bar"]
    result = compare.compare_secrets(src, dst, paths)
    assert len(result) == 1
    row = result[0]
    assert row[0] == "foo/bar"
    assert row[1] == "key"
    assert row[2] == "value"
    assert row[3] == "DIFFERENT"


def test_compare_secrets_missing_in_dst():
    src = FakeVaultManager({"foo/bar": {"key": "value"}})
    dst = FakeVaultManager({})
    paths = ["foo/bar"]
    result = compare.compare_secrets(src, dst, paths)
    assert len(result) == 1
    row = result[0]
    assert row[0] == "foo/bar"
    assert row[1] == "key"
    assert row[2] == "value"
    assert row[3] is None


def test_parse_mount_point_and_base_path():
    parser = argparse.ArgumentParser()
    compare.create_parser(parser)
    args = parser.parse_args([
        '-s', 'http://localhost:8200',
        '-d', 'http://localhost:8201',
        '--mount-point', 'secret-alt',
        '--base-path', 'apps/team'
    ])
    assert args.mount_point == 'secret-alt'
    assert args.base_path == 'apps/team'
