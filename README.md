[![build status](https://github.com/Lucas-C/pre-commit-hooks/workflows/CI/badge.svg)](https://github.com/Lucas-C/pre-commit-hooks/actions?query=branch%3Amaster)

A few useful git hooks to integrate with
[pre-commit](http://pre-commit.com).

**The last version of this hook to support Python 2.7 & 3.6 is v1.1.15**

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Usage](#usage)
  - [insert-license](#insert-license)
- [Handy shell functions](#handy-shell-functions)
- [Useful local hooks](#useful-local-hooks)
  - [Forbid / remove some unicode characters](#forbid--remove-some-unicode-characters)
  - [Bash syntax validation](#bash-syntax-validation)
  - [For Groovy-like Jenkins pipelines](#for-groovy-like-jenkins-pipelines)
  - [Forbid some Javascript keywords for browser retrocompatibility issues](#forbid-some-javascript-keywords-for-browser-retrocompatibility-issues)
  - [CSS](#css)
  - [Some Angular 1.5 checks](#some-angular-15-checks)
- [Development](#development)
  - [Releasing a new version](#releasing-a-new-version)

<!-- mdformat-toc end -->

Hooks specific to a language, or with more dependencies have been extracted
into separate repos:

- https://github.com/Lucas-C/pre-commit-hooks-bandit
- https://github.com/Lucas-C/pre-commit-hooks-go
- https://github.com/Lucas-C/pre-commit-hooks-java
- https://github.com/Lucas-C/pre-commit-hooks-lxml
- https://github.com/Lucas-C/pre-commit-hooks-markup
- https://github.com/Lucas-C/pre-commit-hooks-nodejs
- https://github.com/Lucas-C/pre-commit-hooks-safety

## Usage

```yaml
- repo: https://github.com/Lucas-C/pre-commit-hooks
  rev: v1.1.15
  hooks:
    - id: forbid-crlf
    - id: remove-crlf
    - id: forbid-tabs
    - id: remove-tabs
      args: [--whitespaces-count, '2']  # defaults to: 4
    - id: insert-license
      files: \.groovy$
      args:
        - --license-filepath
        - src/license_header.txt        # defaults to: LICENSE.txt
        - --comment-style
        - //                            # defaults to:  #
```

### insert-license

#### Comment styles

The following styles can be used for example:

- For Java / Javascript / CSS/ C / C++ (multi-line comments) set
  `/*| *| */` ;
- For Java / Javascript / CSS/ C / C++ (single line comments) set `//` ;
- For HTML files: `<!--|  ~|  -->` ;
- For Python: `#` ;
- For Jinja templates: `'{#||#}'` .

#### How to specify in how many lines to search for the license header in each file

You can add `--detect-license-in-X-top-lines=<X>` to search for the license
in top X lines (default 5).

#### Removing old license and replacing it with a new one

In case you want to remove the comment headers introduced by
`insert-license` hook, e.g. because you want to change the wording of your
`LICENSE.txt` and update the comments in your source files:

1. Temporarily add the `--remove-header` arg in your
   `.pre-commit-config.yaml` ;
2. Run the hook on all your files:
   `pre-commit run insert-license --all-files` ;
3. Remove the `--remove-header` arg and update your `LICENSE.txt` ;
4. Re-run the hook on all your files.

#### Fuzzy license matching

In some cases your license files can contain several slightly different
variants of the license - either containing slight modifications or
differently broken lines of the license text.\
By default the plugin does
exact matching when searching for the license and in such case it will add
second licence on top - leaving the non-perfectly matched one in the source
code.\
You can prevent that and add `--fuzzy-match-generates-todo` flag in
which case fuzzy matching is performed based on Levenshtein distance of set
of tokens in expected and actual license text (partial match in two sets is
used).\
The license is detected if the ratio is > than
`--fuzzy-ratio-cut-off` parameter (default 85) - ration corresponds roughly
to how well the expected and actual license match (scale 0 - 100).
Additionally `--fuzzy-match-extra-lines-to-check` lines in this case are
checked for the licence in case it has lines broken differently and takes
more lines (default 3).

If a fuzzy match is found (and no exact match), a TODO comment is inserted
at the beginning of the match found. The comment inserted can be overridden
by `--fuzzy-match-todo-comment=<COMMENT>` flag.\
By default the inserted
comment is
`TODO: This license is not consistent with license used in the project`
Additionally instructions on what to do are inserted in this case.\
By
default instructions
are:\
`Delete the inconsistent license and above line and rerun pre-commit to insert a good license.`.\
You
can change it via `--fuzzy-match-todo-instructions` argument of the hook.

When the TODO comment is committed, pre-commit will fail with appropriate
message. The check will fails systematically if the
`--fuzzy-match-generates-todo` flag is set or not.\
You will need to remove
the TODO comment and licence so that it gets re-added in order to get rid
of the error.

License insertion can be skipped altogether if the file contains the
`SKIP LICENSE INSERTION` in the first X top lines. This can also be
overridden by `--skip-license-insertion-comment=<COMMENT>` flag.

## Handy shell functions

```shell
pre_commit_all_cache_repos () {  # Requires sqlite3
    sqlite3 -header -column ~/.cache/pre-commit/db.db < <(echo -e ".width 50\nSELECT repo, ref, path FROM repos ORDER BY repo;")
}

pre_commit_local_cache_repos () {  # Requires PyYaml & sqlite3
    < $(git rev-parse --show-toplevel)/.pre-commit-config.yaml \
        python -c "from __future__ import print_function; import sys, yaml; print('\n'.join(h['repo']+' '+h['sha'] for h in yaml.load(sys.stdin) if h['repo'] != 'local'))" \
        | while read repo sha; do
            echo $repo
            sqlite3 ~/.cache/pre-commit/db.db "SELECT ref, path FROM repos WHERE repo = '$repo' AND ref = '$sha';"
            echo
        done
}

pre_commit_db_rm_repo () {  # Requires sqlite3
    local repo=${1?'Missing parameter'}
    local repo_path=$(sqlite3 ~/.cache/pre-commit/db.db "SELECT path FROM repos WHERE repo LIKE '%${repo}%';")
    if [ -z "$repo_path" ]; then
        echo "No repository known for repo $repo"
        return 1
    fi
    rm -rf "$repo_path"
    sqlite3 ~/.cache/pre-commit/db.db "DELETE FROM repos WHERE repo LIKE '%${repo}%';";
}
```

## Useful local hooks

### Forbid / remove some unicode characters

```yaml
- repo: local
  hooks:
    - id: forbid-unicode-non-breaking-spaces
      name: Detect unicode non-breaking space character U+00A0 aka M-BM-
      language: system
      entry: perl -ne 'print if $m = /\xc2\xa0/; $t ||= $m; END{{exit $t}}'
      files: ''
    - id: remove-unicode-non-breaking-spaces
      name: Remove unicode non-breaking space character U+00A0 aka M-BM-
      language: system
      entry: perl -pi* -e 's/\xc2\xa0/ /g && ($t = 1) && print STDERR $_; END{{exit
        $t}}'
      files: ''
    - id: forbid-en-dashes
      name: Detect the EXTREMELY confusing unicode character U+2013
      language: system
      entry: perl -ne 'print if $m = /\xe2\x80\x93/; $t ||= $m; END{{exit $t}}'
      files: ''
    - id: remove-en-dashes
      name: Remove the EXTREMELY confusing unicode character U+2013
      language: system
      entry: perl -pi* -e 's/\xe2\x80\x93/-/g && ($t = 1) && print STDERR $_; END{{exit
        $t}}'
      files: ''
```

### Bash syntax validation

```yaml
- repo: local
  hooks:
  - id: check-bash-syntax
    name: Check Shell scripts syntax correctness
    language: system
    entry: bash -n
    files: \.sh$
```

### For Groovy-like Jenkins pipelines

```yaml
- repo: local
  hooks:
  - id: forbid-abstract-classes-and-traits
    name: Ensure neither abstract classes nor traits are used
    language: pygrep
    entry: "^(abstract|trait) "
    files: ^src/.*\.groovy$
```

**Rationale:** `abstract` classes & `traits` do not work in Jenkins
pipelines : cf. https://issues.jenkins-ci.org/browse/JENKINS-39329 &
https://issues.jenkins-ci.org/browse/JENKINS-46145 .

```yaml
- repo: local
  hooks:
  - id: force-JsonSlurperClassic
    name: Ensure JsonSlurperClassic is used instead of non-serializable JsonSlurper
    language: pygrep
    entry: JsonSlurper[^C]
    files: \.groovy$
```

**Rationale:** cf. http://stackoverflow.com/a/38439681/636849

```yaml
- repo: local
  hooks:
    - id: Jenkinsfile-linter
      name: Check Jenkinsfile following the scripted-pipeline syntax using Jenkins
        API
      files: Jenkinsfile
      language: system
      entry: sh -c '! curl --silent $JENKINS_URL/job/MyPipelineName/job/master/1/replay/checkScriptCompile
        --user $JENKINS_USER:$JENKINS_TOKEN --data-urlencode value@Jenkinsfile |
        grep -F "\"status\":\"fail\""'
```

Note: the `$JENKINS_TOKEN` can be retrieved from
`$JENKINS_URL/user/$USER_NAME/configure`

Beware, in 1 case on 6 I faced this unsolved bug with explictly-loaded
libraries: https://issues.jenkins-ci.org/browse/JENKINS-42730 .

Also, there is also a linter for the declarative syntax:
https://jenkins.io/doc/book/pipeline/development/#linter .

### Forbid some Javascript keywords for browser retrocompatibility issues

```yaml
- repo: local
  hooks:
    - id: js-forbid-const
      name: The const keyword is not supported by IE10
      language: pygrep
      entry: 'const '
      files: \.js$
    - id: js-forbid-let
      name: The let keyword is not supported by IE10
      language: pygrep
      entry: 'let '
      files: \.js$
```

### CSS

```yaml
- repo: local
  hooks:
    - id: css-forbid-px
      name: In CSS files, use rem or % over px
      language: pygrep
      entry: px
      files: \.css$
    - id: ot-sanitize-fonts
      name: Calling ot-sanitise on otf/ttf/woff/woff2 font files
      language: system
      entry: sh -c 'type ot-sanitise >/dev/null
        && for font in "$@";
        do echo "$font";
        ot-sanitise "$font"; done
        || echo "WARNING Command ot-sanitise not found - skipping check"'
      files: \.(otf|ttf|woff|woff2)$
```

### Some Angular 1.5 checks

```yaml
- repo: local
  hooks:
    - id: angular-forbid-apply
      name: In AngularJS, use $digest over $apply
      language: pygrep
      entry: \$apply
      files: \.js$
    - id: angular-forbid-ngrepeat-without-trackby
      name: In AngularJS, ALWAYS use 'track by' with ng-repeat
      language: pygrep
      entry: ng-repeat(?!.*track by)
      files: \.html$
    - id: angular-forbid-ngmodel-with-no-dot
      name: In AngularJS, whenever you have ng-model there's gotta be a dot in
        there somewhere
      language: pygrep
      entry: ng-model="?[^.]+[" ]
      files: \.html$
```

## Development

The [GitHub releases](https://github.com/Lucas-C/pre-commit-hooks/releases)
form the historical ChangeLog.

### Releasing a new version

1. Edit version in `setup.py`, `README.md` & `.pre-commit-config.yaml`;
2. `git commit -nam "Version bump to $version" && git tag $version && git push && git push --tags`;
3. Publish a GitHub release.
