from pathlib import Path

import pytest

from hivemux.model import (
  CouldNotListWorkspacesException,
  HivemuxProject,
  HivemuxProjectName,
  HivemuxSession,
  HivemuxWorkspace,
  ProjectIsNotDirectoryException,
)


class TestHivemuxSession:
  @pytest.mark.parametrize(
    "session_name, tmux_session_name",
    [("a_name", "hm_a_name"), (".dot", "hm__dot"), ("a:project", "hm_a_project")],
  )
  def test_from_project_name_to_tmux_session_name(self, session_name: str, tmux_session_name: str) -> None:
    hivemux_session = HivemuxSession.from_project_name(HivemuxProjectName(session_name))

    assert hivemux_session.to_tmux_session_name() == tmux_session_name

  @pytest.mark.parametrize(
    "path, tmux_session_name",
    [
      ("/home/testuser/workspace/hello/", "hm_hello"),
      ("./workspace/.dot", "hm__dot"),
      ("/home/testuser/../othertestuser/:project", "hm__project"),
    ],
  )
  def test_from_path_to_tmux_session_name(self, path: str, tmux_session_name: str) -> None:
    hivemux_session = HivemuxSession.from_path(Path(path))

    assert hivemux_session.to_tmux_session_name() == tmux_session_name

  @pytest.mark.parametrize(
    "session_name, tmux_session_name",
    [("hm__dot", "hm__dot"), ("hm_project_name", "hm_project_name")],
  )
  def test_from_session_name_to_tmux_session_name(self, session_name: str, tmux_session_name: str) -> None:
    hivemux_session = HivemuxSession.from_session_name(session_name)

    assert hivemux_session.to_tmux_session_name() == tmux_session_name

  def test_from_session_fails_does_not_match_pattern(self) -> None:
    session_name_without_prefix = "hello"

    with pytest.raises(ValueError):
      _ = HivemuxSession.from_session_name(session_name_without_prefix)


class TestHivemuxWorkspace:
  def test_create_workspace_raises_with_non_directory(self) -> None:
    with pytest.raises(CouldNotListWorkspacesException):
      _ = HivemuxWorkspace(Path(__file__))

  def test_create_workspace_from_folder(self) -> None:
    path = Path(__file__).parent
    workspace = HivemuxWorkspace(path)
    assert workspace.path == path


class TestHivemuxProject:
  def test_project_does_not_point_to_folder_raises(self) -> None:
    with pytest.raises(ProjectIsNotDirectoryException):
      _ = HivemuxProject(Path(__file__), HivemuxProjectName("some_project"))

  def test_project_points_to_correct_folder(self) -> None:
    project = HivemuxProject(Path(__file__).parent, HivemuxProjectName("project_name"))
    assert project.derive_session_name() == HivemuxSession("tests")
