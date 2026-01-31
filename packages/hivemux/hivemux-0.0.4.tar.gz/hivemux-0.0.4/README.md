# Hivemux

Hivemux is a cli tool allowing easy management of your tmux environments.

What Hivemux provides the following features:
- create pre-defined sessions based on projects found in your workspace
- join pre-started session if one already exists in your environment

## Installation

`pipx install hivemux`

## Configuration

Hivemux can be configured through a TOML file in `$HOME/.config/hivemux/config.toml`.

If you have `XDG_CONFIG_HOME` or `XDG_CONFIG_DIRS` set, Hivemux will look in these locations as described in the [XDG specification](https://specifications.freedesktop.org/basedir/latest/#basics).

Hivemux works well without a config file set, by default, it acts with the default values described below.

_config.toml_
```toml
# Path to your workspace containing all your projects
workspace_path = "~/workspace"

# Pattern to match to find all the projects in the first level of your workspace folder. Must match Python's Path.glob() definition https://docs.python.org/3/library/pathlib.html#pathlib.Path.glob
workspace_markers = ["*/.git"]

# Additional search paths to add to your list of projects. The list is interpreted as glob patterns.
additional_search_paths = []

# .hmrc file used to define how to create the session for all projects
hmrc = """
  new-session -d -c {{cwd}} -s {{session}} -n source nvim .
  new-window -c {{cwd}} -t {{session}} -n shell
  select-window -t {{session}}:source
"""
```

### A note on hmrc

Hivemux creates TMUX sessions based on a template. By default, this template lives in the Hivemux code unless overriden by the config.toml file.
This gives the ability to define a personal and custom session creator.

To override the default hmrc, the config.toml file provides a field called `hmrc` that will be used instead of the default hmrc script provided by Hivemux.

A hmrc file can also be created per project. For example, if your project is under `$HOME/workspace/my_project`, you can override the global hmrc file with a file `$HOME/workspace/my_project/.hmrc`

The content of the hmrc file is parsed through Jinja and therefore allows for some templating.

The following variables are passed to the template:
- session: name of the session
- cwd: absolute path of the project

After the rendering of the template is done, the content is passed directly to tmux without modifications.

The commands defined in the [TMUX documentation](https://man.openbsd.org/OpenBSD-current/man1/tmux.1) can all be used.

#### What must the hmrc file contain

A hmrc script **must** contain the following line at the beginning.

`new-session -d -c {{cwd}} -s {{session}}`

This allows tmux to create the session without attaching to it, allowing Hivemux to finish its execution.

If you want, you can always add [other flags](https://man.openbsd.org/OpenBSD-current/man1/tmux.1#new-session) to the `new-session` command such as `-n` or even a shell command.


## Usage

`hm --help`

`hm list-projects`

`hm attach myproject` or `hm a myproject`

### Shell auto-completion

#### ZSH

In your .zshrc, add the following line.

```bash
eval "$(_HM_COMPLETE=zsh_source hm)"
```

#### bash

In your .bashrc, add the following line.

```bash
eval "$(_HM_COMPLETE=bash_source hm)"
```
