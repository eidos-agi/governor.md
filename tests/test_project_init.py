"""Regression tests for project bootstrap.

Guards the init/set circular bug (fixed 0.4.2): `project-init` with no --path
used to call resolve() — which requires an already-registered project — instead
of initializing at CWD. That made first-time init impossible.
"""

from governor_md._logic import project as P
from governor_md._logic import _session


def test_project_init_no_path_uses_cwd(tmp_path, monkeypatch):
    """init with no --path must create .governor at CWD, not raise 'no project'."""
    _session.get_registry().clear()
    _session.set_default(None)
    monkeypatch.chdir(tmp_path)

    out = P.project_init(project_name="demo")

    assert (tmp_path / ".governor" / "config.yaml").exists()
    assert "project_id:" in out
    # init registers the new project in-session (contract: then call project_set)
    assert len(_session.get_registry()) == 1


def test_project_init_explicit_path(tmp_path):
    """init with an explicit --path initializes there regardless of CWD."""
    _session.get_registry().clear()
    target = tmp_path / "sub"
    target.mkdir()

    P.project_init(project_name="demo2", path=str(target))

    assert (target / ".governor" / "config.yaml").exists()


def test_project_set_after_init(tmp_path, monkeypatch):
    """The full bootstrap: init then set (the sequence that used to deadlock)."""
    _session.get_registry().clear()
    _session.set_default(None)
    monkeypatch.chdir(tmp_path)

    P.project_init(project_name="demo3")
    out = P.project_set(str(tmp_path))

    assert "project_id:" in out
