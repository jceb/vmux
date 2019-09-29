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
import subprocess
import sys
from collections import deque

TMUX_ENVIRON_CACHE = {}
TMUX_ENVIRON_CACHE_GLOBAL = {}


def clear_tmux_environ_cache():
    global TMUX_ENVIRON_CACHE, TMUX_ENVIRON_CACHE_GLOBAL
    TMUX_ENVIRON_CACHE = {}
    TMUX_ENVIRON_CACHE_GLOBAL = {}


def get_tmux_environ(key, is_global=False):
    global TMUX_ENVIRON_CACHE, TMUX_ENVIRON_CACHE_GLOBAL
    if is_global and TMUX_ENVIRON_CACHE_GLOBAL:
        return TMUX_ENVIRON_CACHE_GLOBAL.get(key)
    if TMUX_ENVIRON_CACHE:
        return TMUX_ENVIRON_CACHE.get(key)

    cmd = ['tmux', 'show-environment']
    if is_global:
        cmd.append('-g')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    env = p.communicate()[0].decode('utf-8').split(os.linesep)
    for kv in [v.split('=', 1) for v in env if '=' in v]:
        if len(kv) == 2:
            if is_global:
                TMUX_ENVIRON_CACHE_GLOBAL[kv[0]] = kv[1]
            else:
                TMUX_ENVIRON_CACHE[kv[0]] = kv[1]
    return get_tmux_environ(key, is_global=is_global)


DEBUG = os.environ.get('VMUX_DEBUG')


class Editor(object):
    cmd = None
    cli = None

    def __init__(self, vmux):
        self._vmux = vmux

    @property
    def realdeditor(self):
        return os.path.expandvars(
            os.path.expanduser(
                os.environ.get('VMUX_REALEDITOR_%s' % self.cmd.upper(
                ), os.path.sep + os.path.join('usr', 'bin', self.cmd))))

    @classmethod
    def get_default_editor(cls, editors):
        default_editor = os.environ.get('VMUX_EDITOR', Neovim.cmd)
        for e in editors:
            if e.cmd == default_editor:
                return e

    def __str__(self):
        return self.cmd

    def destroy_session(self):
        pass


class Vim(Editor):
    cmd = 'vim'
    cli = True

    def __init__(self, vmux):
        Editor.__init__(self, vmux)

    @property
    def session_exists(self):
        if not self._vmux.session_exists:
            return False
        if os.path.exists(self.realdeditor):
            try:
                for server in subprocess.check_output(
                    [self.realdeditor,
                    '--serverlist'], stderr=subprocess.PIPE).decode('utf-8').strip().split(os.linesep):
                    if server.upper() == self._vmux.session.upper():
                        return True
            except subprocess.CalledProcessError:
                if DEBUG:
                    import traceback
                    traceback.print_exc()
        return False

    def open(self, args):
        stripped_sep = False
        if args[0] == '--':
            args.pop(0)
            stripped_sep = True
        if args and not stripped_sep and args[0].startswith('-'):
            return subprocess.call(
                [self.realdeditor, '--servername',
                 self._vmux.session.upper()] + args)
        else:
            return subprocess.call([
                self.realdeditor, '--servername',
                self._vmux.session.upper(), '--remote-silent'
            ] + args)

    def new(self, args, new_session=True):
        cmd = [self.realdeditor]
        if new_session:
            self._vmux.new_session(self.cli)
            cmd += ['--servername', self._vmux.session]
        os.execvp(self.realdeditor, cmd + args)


class Gvim(Vim):
    cmd = 'gvim'
    cli = False

    def __init__(self, vmux):
        Vim.__init__(self, vmux)


class Neovim(Editor):
    cmd = 'nvim'
    cli = True

    def __init__(self, vmux):
        self._session_dir = None
        Editor.__init__(self, vmux)
        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)

    @property
    def session_dir(self):
        if not self._session_dir:
            self._session_dir = os.path.expandvars(
                os.path.expanduser(
                    os.environ.get('VMUX_NVIM_SESSION_DIR',
                                   os.path.join(
                                       os.environ.get('HOME'), '.cache', 'tmp',
                                       'nvim_sessions'))))
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

    def open(self, args):

        filenames = []
        commands = []

        done = False

        args = deque(args)
        while args:
            item = args.popleft()

            if done:
                pass
            elif item == '--':
                done = True
                continue
            elif item == '-c':
                commands += [args.popleft()]
                continue
            elif item.startswith('-c'):
                commands += [item[2:]]
                continue
            elif item.startswith('+'):
                commands += [item[1:]]
                continue

            filenames += [os.path.abspath(os.path.expandvars(os.path.expanduser(item)))]

        from pynvim import attach
        nvim = attach('socket', path=self.session_address)

        # get back to normal mode
        nvim.feedkeys(nvim.replace_termcodes('<Esc>'))

        for filename in reversed(filenames):
            nvim.command('e %s' % filename)

        for command in commands:
            nvim.command(command)

    def new(self, args, new_session=True):
        if new_session:
            self._vmux.new_session(self.cli)
        env = {}
        env.update(os.environ)
        if new_session:
            env.update({'NVIM_LISTEN_ADDRESS': self.session_address})
        elif 'NVIM_LISTEN_ADDRESS' in env:
            # make sure that no listening address is specified when starting
            # neovim without a session
            del env['NVIM_LISTEN_ADDRESS']
        cmd = [self.realdeditor] + args
        if DEBUG:
            print(' '.join(cmd))
            print(env)
        os.execve(self.realdeditor, cmd, env)


class NeovimQt(Neovim):
    cmd = 'nvim-qt'
    cli = False


class Kak(Editor):
    cmd = 'kak'
    cli = True

    def __init__(self, vmux):
        self._session_dir = None
        Editor.__init__(self, vmux)
        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)

    def open(self, args):
        if args[0] == '--':
            args.pop(0)
        if args:
            return subprocess.call(
                [self.realdeditor, '-c',
                 self._vmux.session.upper()] + args)

    def new(self, args, new_session=True):
        cmd = [self.realdeditor]
        if new_session:
            self._vmux.new_session(self.cli)
            cmd += ['-s', self._vmux.session]
        os.execvp(self.realdeditor, cmd + args)

    @property
    def session_dir(self):
        if not self._session_dir:
            self._session_dir = os.path.expandvars(
                os.path.expanduser(
                    os.environ.get('VMUX_KAK_SESSION_DIR',
                                   os.path.join(
                                       os.environ.get('HOME'), '.cache', 'tmp',
                                       'kakoune_sessions'))))
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


class Vmux(object):
    def __init__(self):
        self._global = None
        if not os.environ.get('TMUX'):
            # global session can be started outside tmux
            if not self.is_global:
                raise ValueError('No tmux session found')
        self._id = None
        self._pane_id = None
        self._session = None
        self._session_exists = None
        self._global_session = None
        self._shall_select_pane = None

    @property
    def shall_select_pane(self):
        if self._shall_select_pane is None:
            self._shall_select_pane = not bool(
                os.environ.get('VMUX_NOT_SELECT_PANE'))
        return self._shall_select_pane

    @property
    def id(self):
        if not self._id:
            self._id = subprocess.check_output(
                ['tmux', 'display-message', '-p',
                 '#{session_id}']).decode('utf-8').strip().strip('$')
        return self._id

    @property
    def pane_id(self):
        if not self._pane_id:
            self._pane_id = os.environ.get('TMUX_PANE', '')
        return self._pane_id

    @property
    def is_global(self):
        if self._global is None:
            self._global = bool(os.environ.get('VMUX_GLOBAL'))
        return self._global

    @property
    def session_var(self):
        if self.is_global:
            return 'VMUX_SESSION'
        return 'VMUX_SESSION_%s' % self.id

    @property
    def session(self):
        if not self._session and not self.is_global:
            # first try to identify the session from the environment variable
            self._session = get_tmux_environ(self.session_var, is_global=False)
        if not self._session:
            # if the environment didn't produce any result, generate a new
            # session name
            self._session = 'global' if self.is_global else self.pane_id
        return self._session

    @property
    def session_exists(self):
        if self._session_exists is None:
            self._session_exists = ''
            res = get_tmux_environ(self.session_var, is_global=self.is_global)
            if res is not None:
                self._session_exists = res
        return self._session_exists

    @property
    def global_session(self):
        # Attention, this property is fundamentally different from self.session.
        # This property is managed by vmux in order to store the pane id of
        # global sessions
        if not self._global_session:
            self._global_session = get_tmux_environ('VMUX_GLOBAL_PANE', is_global=True)
        return self._global_session

    def destroy_session(self):
        cmd = ['tmux', 'set-environment', '-u']
        if self.is_global:
            cmd.append('-g')
        cmd.append(self.session_var)
        if DEBUG:
            print(' '.join(cmd))
        subprocess.call(cmd)
        self._session = None
        self._session_exists = None
        self._global_session = None
        clear_tmux_environ_cache()

    def new_session(self, cli):
        cmd = ['tmux', 'set-environment']
        if self.is_global:
            cmd.append('-g')
        cmd.extend((self.session_var, self.session))
        if DEBUG:
            print(' '.join(cmd))
        subprocess.call(cmd)
        if self.is_global and cli:
            cmd = [
                'tmux', 'set-environment', '-g', 'VMUX_GLOBAL_PANE',
                self.pane_id
            ]
            if DEBUG:
                print(' '.join(cmd))
            subprocess.call(cmd)

    def select_pane(self, pane_id=None):
        cmd = ('tmux', 'list-panes', '-a', '-F', '#{window_id} #D')
        if DEBUG:
            print(' '.join(cmd))
        if not pane_id:
            pane_id = self.global_session if self.is_global else self.session
        for line in subprocess.check_output(cmd).decode('utf-8').split(
                os.linesep):
            ids = line.split()
            if len(ids) != 2:
                continue
            if ids[1] == pane_id:
                cmd = ('tmux', 'select-window', '-t', ids[0])
                if DEBUG:
                    print(' '.join(cmd))
                subprocess.call(cmd)
                cmd = ('tmux', 'select-pane', '-t', ids[1])
                if DEBUG:
                    print(' '.join(cmd))
                subprocess.call(cmd)
                break


def main():
    v = None
    try:
        v = Vmux()
    except ValueError:
        # ignore error, just start the default editor without any session
        pass
    editors = [Neovim(v), Vim(v), NeovimQt(v), Gvim(v), Kak(v)]
    editor_with_session = None
    default_editor = Editor.get_default_editor(editors)
    if not default_editor:
        print('Unable to find editor %s' % default_editor, file=sys.stderr)
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
            'Running vmux outside TMUX, no enhanced functionality available',
            file=sys.stderr)
        return default_editor.new(sys.argv[1:], new_session=new_session)

    # find session in editor
    if v.session_exists:
        for e in editors:
            if e.session_exists:
                if DEBUG:
                    print(
                        'Found editor with session: %s (%s)' % (e, v.session),
                        file=sys.stderr)
                editor_with_session = e
                break

    # clean up session if it doesn't exist
    if v.session_exists and not editor_with_session:
        if DEBUG:
            print(
                'Destroying session because there is no editor attached to it: %s=%s'
                % (v.session_var, v.session),
                file=sys.stderr)
        v.destroy_session()

    if not v.session_exists:
        # open new session if there is none
        if DEBUG:
            print(
                'Spawning editor with a new session: %s (%s)' %
                (default_editor, v.session),
                file=sys.stderr)
        return default_editor.new(sys.argv[1:], new_session=new_session)
    else:
        new_session = False
        # open files in existing session
        if len(sys.argv) >= 2 and editor_with_session:
            if v.shall_select_pane and editor_with_session.cli:
                if DEBUG:
                    print(
                        'Selecting pane with id %s' % v.pane_id,
                        file=sys.stderr)
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
                pane_id = os.environ.get('TMUX_PANE')
                if DEBUG:
                    print(
                        'Reverting pane selection to id %s' % v.pane_id,
                        file=sys.stderr)
                v.select_pane(pane_id)
        # just the editor was requested, don't start a new session - or the
        # previous command failed to open files in a new session
        if DEBUG:
            print(
                'Spawning editor %s session: %s (%s)' % ({
                    True: 'with a new',
                    False: 'without a'
                }[new_session], default_editor, v.session),
                file=sys.stderr)
        return default_editor.new(sys.argv[1:], new_session=new_session)


if __name__ == "__main__":
    sys.exit(main())
