import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from hivemux.model import HivemuxSession, HivemuxSessions


def new_session(cwd: Path, session_name: HivemuxSession, window_name: str, command: list[str] | None = None) -> None:
  session_cmd = " ".join(command) if command is not None else ""
  _ = subprocess.run(
    [
      "tmux",
      "new-session",
      "-d",
      "-c",
      cwd.absolute(),
      "-s",
      session_name.to_tmux_session_name(),
      "-n",
      window_name,
      session_cmd,
    ],
  )


def new_window(session_name: HivemuxSession, window_name: str) -> None:
  _ = subprocess.run(
    ["tmux", "new-window", "-t", session_name.to_tmux_session_name(), "-n", window_name],
  )


def has_session(session_name: HivemuxSession) -> bool:
  res = subprocess.run(["tmux", "has-session", "-t", session_name.to_tmux_session_name()])
  return res.returncode == 0


def activate_window(session_name: HivemuxSession, window_name: str) -> None:
  _ = subprocess.run(
    ["tmux", "select-window", "-t", f"{session_name.to_tmux_session_name()}:{window_name}"],
  )


def list_sessions() -> HivemuxSessions:
  res = subprocess.run(
    ["tmux", "list-sessions", "-F", "'#{session_name}'"],
    text=True,
    capture_output=True,
  )
  if res.returncode != 0:
    return HivemuxSessions([])
  sessions = [x.removeprefix("'").removesuffix("'") for x in res.stdout.splitlines()]
  return HivemuxSessions(
    [HivemuxSession.from_session_name(x) for x in sessions if HivemuxSession.is_hivemux_session(x)]
  )


def source_tmux_file(tmux_commands: str) -> None:
  with NamedTemporaryFile(
    "w",
  ) as f:
    _ = f.write(tmux_commands)
    f.flush()
    # we need to start the tmux server if no sessions are currently present as source-file does not do it for us
    res = subprocess.run(["tmux", "start", ";", "source-file", str(Path(f.name).absolute())])
    res.check_returncode()


def switch_client(session_name: HivemuxSession) -> None:
  os.execvp("tmux", ["tmux", "switch-client", "-t", session_name.to_tmux_session_name()])


def attach(session_name: HivemuxSession) -> None:
  os.execvp("tmux", ["tmux", "attach", "-t", session_name.to_tmux_session_name()])
