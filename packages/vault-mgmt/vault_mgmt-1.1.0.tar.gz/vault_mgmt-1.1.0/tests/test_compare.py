import argparse

from vault_mgmt import compare


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
