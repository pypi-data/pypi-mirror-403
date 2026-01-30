# git-smart-clone

A simple git extension that clones a git directory to sub folder based on the git url.

## Installation

To install use [pipx](https://github.com/pypa/pipx):

```shell
pipx install git-smart-clone
```

## Usage

By default this will clone a git repo into your `~/src` directory in the format _hostname_/_owner_/_repo name_. This can be overridden with the environmental variable: `GIT_SMART_CLONE_BASE_PATH`.

So this command 

```shell
git smart-clone https://github.com/sam-phinizy/git-smart-clone
```

would clone this repo to this location on your computer:

`~/src/github.com/sam-phinizy/git-smart-clone`.

Note: Any flags passed to the command will be passed through to `git`.


## License
MIT
[LICENSE](LICENSE)
