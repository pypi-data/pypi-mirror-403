from vault_mgmt import cli


def test_get_version():
    version = cli.get_version()
    assert isinstance(version, str)
    assert version


def test_create_parser():
    parser = cli.create_parser()
    assert parser is not None


def test_main_runs_compare(monkeypatch):
    # Patch sys.argv to simulate CLI call
    monkeypatch.setattr('sys.argv', ['vault-mgmt', 'compare', '-s', 'http://localhost:8200', '-d', 'http://localhost:8201'])
    try:
        cli.main()
    except SystemExit as e:
        # Should not exit with error
        assert e.code in (None, 0)


def test_main_runs_sync(monkeypatch):
    # Patch sys.argv to simulate CLI call
    monkeypatch.setattr('sys.argv', ['vault-mgmt', 'sync', '-s', 'http://localhost:8200', '-d', 'http://localhost:8201'])
    try:
        cli.main()
    except SystemExit as e:
        # Should not exit with error
        assert e.code in (None, 0)


def test_main_runs_rollout(monkeypatch):
    # Patch sys.argv to simulate CLI call
    monkeypatch.setattr('sys.argv', ['vault-mgmt', 'rollout', '--vault-addr', 'http://localhost:8200'])
    try:
        cli.main()
    except SystemExit as e:
        # Should not exit with error
        assert e.code in (None, 0)
