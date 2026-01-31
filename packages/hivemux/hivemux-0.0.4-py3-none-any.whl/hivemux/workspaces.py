from dataclasses import dataclass
from pathlib import Path

from hivemux.model import HivemuxProject, HivemuxProjectName, HivemuxWorkspace


@dataclass(frozen=True)
class Workspace:
  human_friendly_name: str
  path: Path


def list_workspaces(
  base_workspace_path: HivemuxWorkspace, additional_search_paths: list[Path], workspace_markers: list[str]
) -> set[HivemuxProject]:
  projects: set[HivemuxProject] = set()
  for pattern in workspace_markers:
    for match in base_workspace_path.path.glob(pattern):
      parent_path = match.parent
      projects.add(HivemuxProject(path=parent_path, human_friendly_name=HivemuxProjectName(parent_path.name.lower())))
  for search_path in additional_search_paths:
    projects.add(HivemuxProject(path=search_path, human_friendly_name=HivemuxProjectName(search_path.name.lower())))
  return projects
