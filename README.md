A few useful git hooks to integrate with [pre-commit](http://pre-commit.com).

Hooks that require Python dependencies have been extracted into separate repos:

- https://github.com/Lucas-C/pre-commit-hooks-css
- https://github.com/Lucas-C/pre-commit-hooks-lxml

## Usage

Check `.pre-commit-config.yaml` in this repo for usage examples and useful local hooks.

For the _remove-tabs_ hook, the number of whitespaces to substitute tabs with can be configured (it defaults to 4):

        args: [ --whitespaces-count, 2 ]
