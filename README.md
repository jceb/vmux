# vmux
vim/neovim session handler within tmux

# Demo

[![asciicast](https://asciinema.org/a/46634.png)](https://asciinema.org/a/46634)

# Features

* Each `tmux` session has its own editor session
* Supports [vim](http://vim.org/) and [neovim](http://neovim.org/)
* Seamless integration with `vim` and `nvim` through wrapper scripts that
  directly call `vmux` - keep your muscle's memory :-)
* Once a session has been started in one editor, e.g. `nvim`, the session will
  be reused even if the other editor is called, e.g. `vim`
* A new session is started if the old session doesn't exist anymore

# Installation

Clone the repository and install vmux:

    git clone https://github.com/jceb/vmux.git
    cd vmux
    make DESTDIR=~/.local install

    # if wrapper scripts are desired, install them as well
    make DESTDIR=~/.local all

    # add ~/.local/bin to PATH variable
    export PATH="${HOME}/.local/bin:${PATH}"

# Usage

Start editor session through `vmux` or `vim` and `nvim` wrapper scripts:

    tmux
    vmux MYFILE
    # split tmux window
    vmux MY_OTHERFILE

# Similar projects

* [tmux-omnivim](https://github.com/andy-lang/tmux-omnivim)
