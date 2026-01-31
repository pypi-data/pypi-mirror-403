import os
import sys
from typing import override

import click
from click.shell_completion import CompletionItem

from hivemux import project as hivemux_project
from hivemux import tmux, workspaces
from hivemux import config
from hivemux.config import read_config
from hivemux.model import HivemuxProject, HivemuxWorkspace


@click.group()
def cli() -> None:
  pass


# @cli.command("list-sessions")
# def list_sessions() -> None:
#   sessions = tmux.list_sessions()
#   for session in sessions:
#     print(session)
#


def list_available_projects_from_config() -> set[HivemuxProject]:
  config = read_config()
  return workspaces.list_workspaces(
    HivemuxWorkspace(config.workspace_path),
    additional_search_paths=config.additional_search_paths,
    workspace_markers=config.workspace_markers,
  )


@cli.command("list-projects")
def list_projects() -> None:
  available_projects = list_available_projects_from_config()
  for workspace in sorted(available_projects, key=lambda x: x.human_friendly_name.lower()):
    print(workspace.human_friendly_name)


class ProjectVarType(click.ParamType):
  name = "project"

  @override
  def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
    return [
      CompletionItem(p.human_friendly_name)
      for p in list_available_projects_from_config()
      if p.human_friendly_name.startswith(incomplete)
    ]


@cli.command("attach")
@click.argument("project", type=ProjectVarType())
def attach(project: str) -> None:
  join_session(project)


@cli.command("a")
@click.argument("project", type=ProjectVarType())
def a(project: str) -> None:
  join_session(project)


def join_session(project: str) -> None:
  conf = config.read_config()
  project_manager = hivemux_project.ProjectManager(conf)
  available_projects = list_available_projects_from_config()
  matching_project = next(iter([p for p in available_projects if p.human_friendly_name == project.lower()]), None)
  if matching_project is None:
    print(f"Project {project} does not exist in workspace")
    sys.exit(1)
  current_tmux_sessions = tmux.list_sessions()
  possible_session = current_tmux_sessions.get_session_for_project(matching_project)
  if possible_session is None:
    possible_session = project_manager.start_new_project(matching_project)

  if "TMUX" in os.environ:
    tmux.switch_client(possible_session)
  else:
    tmux.attach(possible_session)
