#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vmux
#  Vim/Neovim sessions with the help of tmux
#
# Depends: tmux, vim/nvim
#
# Copyright (C) 2016 Jan Christoph Ebersbach
#
# http://www.e-jc.de/
#
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import subprocess
import sys

TMUX_ENVIRON_CACHE = {}
TMUX_ENVIRON_CACHE_GLOBAL = {}
DEBUG = os.environ.get("VMUX_DEBUG")


def clear_tmux_environ_cache():
    global TMUX_ENVIRON_CACHE, TMUX_ENVIRON_CACHE_GLOBAL
    TMUX_ENVIRON_CACHE = {}
    TMUX_ENVIRON_CACHE_GLOBAL = {}


def get_tmux_environ(key: str, is_global: bool = False) -> str | None:
    global TMUX_ENVIRON_CACHE, TMUX_ENVIRON_CACHE_GLOBAL
    if is_global and TMUX_ENVIRON_CACHE_GLOBAL:
        return TMUX_ENVIRON_CACHE_GLOBAL.get(key)
    if TMUX_ENVIRON_CACHE:
        return TMUX_ENVIRON_CACHE.get(key)

    cmd = ["tmux", "show-environment"]
    if is_global:
        cmd.append("-g")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    env = p.communicate()[0].decode("utf-8").split(os.linesep)
    for kv in [v.split("=", 1) for v in env if "=" in v]:
        if len(kv) == 2:
            if is_global:
                TMUX_ENVIRON_CACHE_GLOBAL[kv[0]] = kv[1]
            else:
                TMUX_ENVIRON_CACHE[kv[0]] = kv[1]
    return get_tmux_environ(key, is_global=is_global)


def args_to_absolute_paths(args: list[str]):
    abs_args = []
    for arg in args:
        if arg.startswith("-") or os.path.isabs(arg):
            abs_args.append(arg)
        else:
            abs_args.append(os.path.join(os.getcwd(), arg))
    return abs_args


class Vmux(object):
    _global: bool | None = None
    _id: str = ""
    _pane_id: str = ""
    _session: str = ""
    _session_exists: str | None = None
    _global_session: str | None = None
    _shall_select_pane: bool | None = None

    def __init__(self):
        super().__init__()
        if not os.environ.get("TMUX"):
            # global session can be started outside tmux
            if not self.is_global:
                raise ValueError("No tmux session found")

    @property
    def shall_select_pane(self) -> bool:
        if self._shall_select_pane is None:
            self._shall_select_pane = not bool(os.environ.get("VMUX_NOT_SELECT_PANE"))
        return self._shall_select_pane

    @property
    def id(self) -> str:
        if not self._id:
            self._id = (
                subprocess.check_output(
                    ["tmux", "display-message", "-p", "#{session_id}"]
                )
                .decode("utf-8")
                .strip()
                .strip("$")
            )
        return self._id

    @property
    def pane_id(self) -> str:
        if not self._pane_id:
            self._pane_id = os.environ.get("TMUX_PANE", "")
        return self._pane_id

    @property
    def is_global(self) -> bool:
        if self._global is None:
            self._global = bool(os.environ.get("VMUX_GLOBAL"))
        return self._global

    @property
    def session_var(self) -> str:
        if self.is_global:
            return "VMUX_SESSION"
        return "VMUX_SESSION_%s" % self.id

    @property
    def session(self) -> str:
        if not self._session and not self.is_global:
            # first try to identify the session from the environment variable
            tmp_session = get_tmux_environ(self.session_var, is_global=False)
            if tmp_session is not None:
                self._session = tmp_session
        if not self._session:
            # if the environment didn't produce any result, generate a new
            # session name
            self._session = "global" if self.is_global else self.pane_id
        return self._session

    @property
    def session_exists(self) -> str:
        if self._session_exists is None:
            self._session_exists = ""
            res = get_tmux_environ(self.session_var, is_global=self.is_global)
            if res is not None:
                self._session_exists = res
        return self._session_exists

    @property
    def global_session(self) -> str | None:
        # Attention, this property is fundamentally different from self.session.
        # This property is managed by vmux in order to store the pane id of
        # global sessions
        if not self._global_session:
            self._global_session = get_tmux_environ("VMUX_GLOBAL_PANE", is_global=True)
        return self._global_session

    def destroy_session(self) -> None:
        cmd = ["tmux", "set-environment", "-u"]
        if self.is_global:
            cmd.append("-g")
        cmd.append(self.session_var)
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
        subprocess.call(cmd)
        self._session = ""
        self._session_exists = None
        self._global_session = None
        clear_tmux_environ_cache()

    def new_session(self, cli) -> None:
        cmd = ["tmux", "set-environment"]
        if self.is_global:
            cmd.append("-g")
        cmd.extend((self.session_var, self.session))
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
        subprocess.call(cmd)
        if self.is_global and cli:
            cmd = ["tmux", "set-environment", "-g", "VMUX_GLOBAL_PANE", self.pane_id]
            if DEBUG:
                print("Executing command:", " ".join(cmd), file=sys.stderr)
            subprocess.call(cmd)

    def select_pane(self, pane_id: str | None = "") -> None:
        cmd = ("tmux", "list-panes", "-a", "-F", "#{window_id} #D")
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
        if not pane_id:
            pane_id = self.global_session if self.is_global else self.session
        for line in subprocess.check_output(cmd).decode("utf-8").split(os.linesep):
            ids = line.split()
            if len(ids) != 2:
                continue
            if ids[1] == pane_id:
                cmd = ("tmux", "select-window", "-t", ids[0])
                if DEBUG:
                    print("Executing command:", " ".join(cmd), file=sys.stderr)
                subprocess.call(cmd)
                cmd = ("tmux", "select-pane", "-t", ids[1])
                if DEBUG:
                    print("Executing command:", " ".join(cmd), file=sys.stderr)
                subprocess.call(cmd)
                break


def main():
    v = None
    try:
        v = Vmux()
    except ValueError:
        # ignore error, just start the default editor without any session
        pass
    editors = [Neovim(v)]
    # editors = [Nvr(v), Neovim(v), Vim(v), NeovimQt(v), Gvim(v), Kak(v)]
    editor_with_session = None
    default_editor = Editor.get_default_editor(editors)
    if not default_editor:
        print("Unable to find editor %s" % default_editor, file=sys.stderr)
        return 3
    new_session = True

    # Behavior:
    # Outside of tmux:
    # - open a new instance without spawning a session
    # vim
    # - without existing session - open a new session
    # - with an existing session - open a new instance without spawning a session
    # vim FILES
    # - without existing session - open a new session
    # - with an existing session - open files in existing session
    if not v:
        new_session = False
        print(
            "Running vmux outside TMUX, no enhanced functionality available",
            file=sys.stderr,
        )
        return default_editor.new(sys.argv[1:], new_session=new_session)

    # find session in editor
    if v.session_exists:
        for e in editors:
            if e.session_exists:
                if DEBUG:
                    print(
                        "Found editor with session: %s (%s)" % (e, v.session),
                        file=sys.stderr,
                    )
                editor_with_session = e
                break

    # clean up session if it doesn't exist
    if v.session_exists and not editor_with_session:
        if DEBUG:
            print(
                "Destroying session because there is no editor attached to it: %s=%s"
                % (v.session_var, v.session),
                file=sys.stderr,
            )
        v.destroy_session()

    if not v.session_exists:
        # open new session if there is none
        if DEBUG:
            print(
                "Spawning editor with a new session: %s (%s)"
                % (default_editor, v.session),
                file=sys.stderr,
            )
        return default_editor.new(sys.argv[1:], new_session=new_session)
    else:
        new_session = False
        # open files in existing session
        if len(sys.argv) >= 2 and editor_with_session:
            if v.shall_select_pane and editor_with_session.cli:
                if DEBUG:
                    print("Selecting pane with id %s" % v.pane_id, file=sys.stderr)
                v.select_pane()
            try:
                return editor_with_session.open(sys.argv[1:])
            except ConnectionRefusedError:
                if DEBUG:
                    import traceback

                    traceback.print_exc()
                v.destroy_session()
                editor_with_session.destroy_session()
                new_session = True
            except Exception:
                import traceback

                traceback.print_exc()
                return 1
            if v.shall_select_pane and editor_with_session.cli:
                pane_id = os.environ.get("TMUX_PANE")
                if DEBUG:
                    print(
                        "Reverting pane selection to id %s" % v.pane_id, file=sys.stderr
                    )
                v.select_pane(pane_id)
        # just the editor was requested, don't start a new session - or the
        # previous command failed to open files in a new session
        if DEBUG:
            print(
                "Spawning editor %s session: %s (%s)"
                % (
                    {True: "with a new", False: "without a"}[new_session],
                    default_editor,
                    v.session,
                ),
                file=sys.stderr,
            )
        return default_editor.new(sys.argv[1:], new_session=new_session)


class Editor(object):
    def __init__(self, vmux):
        self.cmd: str
        self.cli: bool
        self._vmux: Vmux = vmux
        super().__init__()

    @property
    def realdeditor(self) -> str:
        default = self.cmd
        editor = os.path.expandvars(
            os.path.expanduser(
                os.environ.get("VMUX_REALEDITOR_%s" % self.cmd.upper(), default)
            )
        )
        if editor:
            if not os.path.exists(editor):
                editor = shutil.which(editor)
                return editor if editor else self.cmd
            return editor
        else:
            editor = shutil.which(self.cmd)
            return editor if editor else self.cmd

    @classmethod
    def get_default_editor(cls, editors: list):
        default_editor = os.environ.get("VMUX_EDITOR", Nvr.cmd)
        for editor in editors:
            if editor.cmd == default_editor:
                return editor

    def __str__(self):
        return self.cmd

    def destroy_session(self):
        pass


class Vim(Editor):
    cmd = "vim"
    cli = True

    def __init__(self, vmux):
        super().__init__(vmux)

    @property
    def session_exists(self):
        print("session_exists", file=sys.stderr)
        if not self._vmux.session_exists:
            return False
        if os.path.exists(self.realdeditor):
            try:
                if DEBUG:
                    print(
                        "Executing command:",
                        " ".join([self.realdeditor, "--serverlist"]),
                        file=sys.stderr,
                    )
                for server in (
                    subprocess.check_output(
                        [self.realdeditor, "--serverlist"], stderr=subprocess.PIPE
                    )
                    .decode("utf-8")
                    .strip()
                    .split(os.linesep)
                ):
                    if server.upper() == self._vmux.session.upper():
                        return True
            except subprocess.CalledProcessError:
                if DEBUG:
                    import traceback

                    traceback.print_exc()
        return False

    def open(self, args: list[str]):
        stripped_sep = False
        if args[0] == "--":
            args.pop(0)
            stripped_sep = True
        cmd = [self.realdeditor, "--servername", self._vmux.session.upper()]
        if args and not stripped_sep and args[0].startswith("-"):
            cmd += args_to_absolute_paths(args)
        else:
            cmd += ["--remote-silent"] + args_to_absolute_paths(args)
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
        os.execvp(cmd[0], cmd)

    def new(self, args, new_session=True):
        cmd = [self.realdeditor]
        if new_session:
            self._vmux.new_session(self.cli)
            cmd += ["--servername", self._vmux.session]
        cmd += args_to_absolute_paths(args)
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
        os.execvp(self.realdeditor, cmd)


class Gvim(Vim):
    cmd = "gvim"
    cli = False

    def __init__(self, vmux):
        Vim.__init__(self, vmux)


class Neovim(Editor):
    cmd = "nvim"
    cli = True
    _session_dir: str = ""

    def __init__(self, vmux):
        super().__init__(vmux)

    @property
    def session_dir(self) -> str:
        if not self._session_dir:
            default = os.path.join(
                os.environ.get("HOME", "/tmp"), ".cache", "tmp", "nvim_sessions"
            )
            self._session_dir = os.path.expandvars(
                os.path.expanduser(os.environ.get("VMUX_NVIM_SESSION_DIR", default))
            )
        if self._session_dir and not os.path.exists(self._session_dir):
            os.makedirs(self._session_dir)
        return self._session_dir

    @property
    def session_exists(self) -> bool:
        if not self._vmux.session_exists:
            return False
        return os.path.exists(self.session_address)

    @property
    def session_address(self) -> str:
        return os.path.join(self.session_dir, self._vmux.session)

    def destroy_session(self) -> None:
        if os.path.exists(self.session_address):
            os.remove(self.session_address)

    def open(self, args: list[str]):
        cmd = [
            self.realdeditor,
            "--server",
            self.session_address,
            "--remote-silent",
        ] + args_to_absolute_paths(args)
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
        return subprocess.call(cmd)

    def new(self, args: list[str], new_session: bool = True):
        if not args:
            new_session = True
        if new_session:
            self._vmux.new_session(self.cli)
        cmd = [self.realdeditor]
        env = {}
        env.update(os.environ)
        if not new_session and "NVIM_LISTEN_ADDRESS" in env:
            # make sure that no listening address is specified when starting
            # neovim without a session
            del env["NVIM_LISTEN_ADDRESS"]
        if new_session:
            env.update({"NVIM_LISTEN_ADDRESS": self.session_address})
            cmd.extend(["--listen", self.session_address])
        else:
            cmd.extend(["--server", self.session_address, "--remote-silent"])
        cmd.extend(args_to_absolute_paths(args))
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
            print(env, file=sys.stderr)
        os.execve(self.realdeditor, cmd, env)


class Nvr(Neovim):
    cmd = "nvr"

    def __init__(self, vmux):
        super().__init__(vmux)

    @property
    def session_dir(self) -> str:
        if not self._session_dir:
            default = os.path.join(
                os.environ.get("HOME", "/tmp"), ".cache", "tmp", "nvr_sessions"
            )
            self._session_dir = os.path.expandvars(
                os.path.expanduser(os.environ.get("VMUX_NVR_SESSION_DIR", default))
            )
        if self._session_dir and not os.path.exists(self._session_dir):
            os.makedirs(self._session_dir)
        return self._session_dir

    def new(self, args: list[str], new_session: bool = True):
        if not args:
            new_session = True
        if new_session:
            self._vmux.new_session(self.cli)
        cmd = [self.realdeditor]
        env = {}
        env.update(os.environ)
        if not new_session and "NVIM_LISTEN_ADDRESS" in env:
            # make sure that no listening address is specified when starting
            # neovim without a session
            del env["NVIM_LISTEN_ADDRESS"]
        if new_session:
            env.update({"NVIM_LISTEN_ADDRESS": self.session_address})
        else:
            cmd.extend(["--servername", self.session_address, "--remote-silent"])
        cmd.extend(args_to_absolute_paths(args))
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
            print(env, file=sys.stderr)
        os.execve(cmd[0], cmd, env)

    def open(self, args):
        cmd = [
            self.realdeditor,
            "--servername",
            self.session_address,
        ] + args_to_absolute_paths(args)
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
        os.execvp(cmd[0], cmd)


class NeovimQt(Neovim):
    cmd = "nvim-qt"
    cli = False

    def __init__(self, vmux):
        super().__init__(vmux)


class Gnvim(Neovim):
    cmd = "gnvim"
    cli = False

    def __init__(self, vmux):
        super().__init__(vmux)


class Kak(Editor):
    cmd = "kak"
    cli = True
    _session_dir: str = ""

    def __init__(self, vmux):
        super().__init__(vmux)

    def open(self, args):
        if DEBUG:
            print(
                "Executing command:",
                " ".join([self.realdeditor, "-c", self._vmux.session.upper()]),
                file=sys.stderr,
            )
        return subprocess.call(
            [self.realdeditor, "-c", self._vmux.session.upper()]
            + args_to_absolute_paths(args)
        )

    def new(self, args: list[str], new_session: bool = True):
        cmd = [self.realdeditor]
        if new_session:
            self._vmux.new_session(self.cli)
            cmd += ["-s", self._vmux.session]
        if DEBUG:
            print("Executing command:", " ".join(cmd), file=sys.stderr)
        os.execvp(self.realdeditor, cmd + args_to_absolute_paths(args))

    @property
    def session_dir(self):
        if not self._session_dir:
            default = os.path.join(
                os.environ.get("HOME", "/tmp"), ".cache", "tmp", "kakoune_sessions"
            )

            self._session_dir = os.path.expandvars(
                os.path.expanduser(os.environ.get("VMUX_KAK_SESSION_DIR", default))
            )
        if self._session_dir and not os.path.exists(self._session_dir):
            os.makedirs(self._session_dir)
        return self._session_dir

    @property
    def session_exists(self):
        if not self._vmux.session_exists:
            return False
        return os.path.exists(self.session_address)

    @property
    def session_address(self):
        return os.path.join(self.session_dir, self._vmux.session)

    def destroy_session(self):
        if os.path.exists(self.session_address):
            os.remove(self.session_address)


if __name__ == "__main__":
    sys.exit(main())
