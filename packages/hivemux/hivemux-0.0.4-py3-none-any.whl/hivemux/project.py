from dataclasses import dataclass

from jinja2 import Template

from hivemux.config import Config
from hivemux.model import HivemuxProject, HivemuxSession
from hivemux.tmux import source_tmux_file


@dataclass(frozen=True)
class ProjectManager:
  config: Config

  def start_new_project(self, project: HivemuxProject) -> HivemuxSession:
    session_name = project.derive_session_name()
    possible_project_hmrc = project.path / ".hmrc"
    if possible_project_hmrc.exists():
      hmrc = possible_project_hmrc.read_text()
    else:
      hmrc = self.config.hmrc
    template = Template(hmrc)
    rendered_rc = template.render(session=session_name.to_tmux_session_name(), cwd=str(project.path.absolute()))  # pyright: ignore[reportAny]
    source_tmux_file(rendered_rc)
    return session_name
