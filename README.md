A few useful git hooks to integrate with [pre-commit](http://pre-commit.com).

## Usage

Check `.pre-commit-config.yaml` in this repo for usage examples, including the following local hooks:

- angular-forbid-apply
- angular-forbid-ngmodel-with-no-dot

For the _remove-tabs_ hook, the number of whitespaces to substitute tabs with can be configured (it defaults to 4):

        args: [ --whitespaces-count, 2 ]
