import argparse

from vault_mgmt import sync


def test_create_parser():
    parser = argparse.ArgumentParser()
    sync.create_parser(parser)
    assert isinstance(parser, argparse.ArgumentParser)


def test_main_help(capsys):
    parser = argparse.ArgumentParser()
    sync.create_parser(parser)
    try:
        parser.parse_args(['--help'])
    except SystemExit as e:
        assert e.code == 0


def test_main_minimal(monkeypatch):
    parser = argparse.ArgumentParser()
    sync.create_parser(parser)
    args = parser.parse_args([
        '-s', 'http://localhost:8200',
        '-d', 'http://localhost:8201'
    ])
    sync.main(args)


def test_parse_auth_options():
    parser = argparse.ArgumentParser()
    sync.create_parser(parser)
    args = parser.parse_args([
        '-s', 'http://localhost:8200',
        '-d', 'http://localhost:8201',
        '--auth-config', 'auth.yml',
        '--source-auth-method', 'kubernetes',
        '--source-auth-mount', 'k8s-a',
        '--source-auth-role', 'read',
        '--source-auth-jwt-path', '/tmp/jwt',
        '--dest-auth-method', 'kubernetes',
        '--dest-auth-mount', 'k8s-b',
        '--dest-auth-role', 'write',
        '--dest-auth-jwt-path', '/tmp/jwt-dst',
    ])
    assert args.auth_config == 'auth.yml'
    assert args.source_auth_method == 'kubernetes'
    assert args.source_auth_mount == 'k8s-a'
    assert args.source_auth_role == 'read'
    assert args.source_auth_jwt_path == '/tmp/jwt'
    assert args.dest_auth_method == 'kubernetes'
    assert args.dest_auth_mount == 'k8s-b'
    assert args.dest_auth_role == 'write'
    assert args.dest_auth_jwt_path == '/tmp/jwt-dst'
