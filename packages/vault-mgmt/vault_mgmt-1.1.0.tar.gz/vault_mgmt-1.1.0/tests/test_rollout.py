import argparse

from vault_mgmt import rollout


def test_create_parser():
    parser = argparse.ArgumentParser()
    rollout.create_parser(parser)
    assert isinstance(parser, argparse.ArgumentParser)


def test_main_help(capsys):
    parser = argparse.ArgumentParser()
    rollout.create_parser(parser)
    try:
        parser.parse_args(['--help'])
    except SystemExit as e:
        assert e.code == 0


def test_main_minimal(monkeypatch):
    parser = argparse.ArgumentParser()
    rollout.create_parser(parser)
    args = parser.parse_args([
        'vault', '--vault-addr', 'http://localhost:8200', '--strict'
    ])
    rollout.main(args)


def test_parse_auth_options():
    parser = argparse.ArgumentParser()
    rollout.create_parser(parser)
    args = parser.parse_args([
        'vault',
        '--vault-addr', 'http://localhost:8200',
        '--auth-config', 'auth.yml',
        '--auth-method', 'kubernetes',
        '--auth-mount', 'k8s-a',
        '--auth-role', 'rollout-role',
        '--auth-jwt-path', '/tmp/jwt',
    ])
    assert args.auth_config == 'auth.yml'
    assert args.auth_method == 'kubernetes'
    assert args.auth_mount == 'k8s-a'
    assert args.auth_role == 'rollout-role'
    assert args.auth_jwt_path == '/tmp/jwt'
