A few useful git hooks to integrate with [pre-commit](http://pre-commit.com).

##Usage

Put either of the following snippets into your `.pre-commit-config.yaml`:

    - repo: git://github.com/Lucas-C/pre-commit-hooks
      sha: cf87d6c9fc3d5c8324fafa7ca46be822486fbd93
      hooks:
      - id: forbid-crlf

    - repo: git://github.com/Lucas-C/pre-commit-hooks
      sha: cf87d6c9fc3d5c8324fafa7ca46be822486fbd93
      hooks:
      - id: remove-crlf

