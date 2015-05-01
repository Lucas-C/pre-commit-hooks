A few useful git hooks to integrate with [pre-commit](http://pre-commit.com).

##Usage

Put either of the following snippets into your `.pre-commit-config.yaml`:

    - repo: git://github.com/Lucas-C/pre-commit-hooks
      sha: <latest commit sha>
      hooks:
      - id: forbid-crlf

    - repo: git://github.com/Lucas-C/pre-commit-hooks
      sha: <latest commit sha>
      hooks:
      - id: remove-crlf

