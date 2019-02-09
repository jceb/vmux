# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]
### Changed
- Enhance argument parsing for neovim (by @joshbode)
- Stop looking for session if positive match is found (by @joshbode)

## [v1.0]
### Added
- Add support for nvim-qt
- Add CHANGELOG.md

### Changed
- Rename traget install-wrapper to install-scripts
- Make Makefile output more verbose to help the user understand what's
  happening
- Use SCRIPTS variable in Makefile instead of referring to the
  individual scripts in targets

### Fixed
- Fix endless loop when reading global variables
- Remove unused variable
