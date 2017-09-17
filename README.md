A few useful git hooks to integrate with [pre-commit](http://pre-commit.com).

<!-- toc -->

- [Usage](#usage)
  * [insert-license](#insert-license)
- [Handy shell functions](#handy-shell-functions)
- [Useful local hooks](#useful-local-hooks)
  * [Forbid / remove some unicode characters](#forbid--remove-some-unicode-characters)
  * [Bash syntax validation](#bash-syntax-validation)
  * [For Groovy-like Jenkins pipelines](#for-groovy-like-jenkins-pipelines)
  * [Forbid some Javascript keywords for browser retrocompatibility issues](#forbid-some-javascript-keywords-for-browser-retrocompatibility-issues)
  * [CSS](#css)
  * [Some Angular 1.5 checks](#some-angular-15-checks)

<!-- tocstop -->

Hooks that require Python dependencies, or specific to a language, have been extracted into separate repos:

- https://github.com/Lucas-C/pre-commit-hooks-bandit
- https://github.com/Lucas-C/pre-commit-hooks-go
- https://github.com/Lucas-C/pre-commit-hooks-java
- https://github.com/Lucas-C/pre-commit-hooks-lxml
- https://github.com/Lucas-C/pre-commit-hooks-nodejs
- https://github.com/Lucas-C/pre-commit-hooks-safety

## Usage

    -   repo: git://github.com/Lucas-C/pre-commit-hooks
        sha: v1.1.4
        hooks:
        -   id: forbid-crlf
        -   id: remove-crlf
        -   id: forbid-tabs
        -   id: remove-tabs
            args: [ --whitespaces-count, 2 ]  # defaults to: 4
        -   id: insert-license
            files: \.groovy$
            args:
            - --license-filepath
            - src/license_header.txt          # defaults to: LICENSE.txt
            - --comment-style
            - //                              # defaults to: #

### insert-license

For Java / Javascript / CSS, set `--comment-style /*| *| */`.
For HTML files: `--comment-style <!--|  ~|  -->`.

In case you want to remove the comment headers introduced by the `insert-license` hook,
e.g. because you want to change the wording of your `LICENSE.txt` and update the comments in your source files:

1. temporarily add the `--remove-header` arg in your `.pre-commit-config.yaml`
2. run the hook on all your files: `pre-commit run insert-license --all-files`
3. remove the `--remove-header` arg and update your `LICENSE.txt`
4. re-run the hook on all your files


## Handy shell functions
```
pre_commit_all_cache_repos () {  # Requires sqlite3
    sqlite3 -column ~/.cache/pre-commit/db.db "SELECT repo, ref, path FROM repos GROUP BY repo ORDER BY ref;"
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
    local repo_path=$(sqlite3 ~/.cache/pre-commit/db.db "SELECT path FROM repos WHERE repo = '$repo';")
    if [ -z "$repo_path" ]; then
        echo "No repository known for repo $repo"
        return 1
    fi
    rm -rf "$repo_path"
    sqlite3 ~/.cache/pre-commit/db.db "DELETE FROM repos WHERE repo = '$repo';";
}
```

## Useful local hooks

### Forbid / remove some unicode characters

    -   repo: local
        hooks:
        -   id: forbid-unicode-non-breaking-spaces
            name: Detect unicode non-breaking space character U+00A0 aka M-BM-
            language: system
            entry: perl -ne 'print if $m = /\xc2\xa0/; $t ||= $m; END{{exit $t}}'
            files: ''
        -   id: remove-unicode-non-breaking-spaces
            name: Remove unicode non-breaking space character U+00A0 aka M-BM-
            language: system
            entry: perl -pi* -e 's/\xc2\xa0/ /g && ($t = 1) && print STDERR $_; END{{exit
                $t}}'
            files: ''
        -   id: forbid-en-dashes
            name: Detect the EXTREMELY confusing unicode character U+2013
            language: system
            entry: perl -ne 'print if $m = /\xe2\x80\x93/; $t ||= $m; END{{exit $t}}'
            files: ''
        -   id: remove-en-dashes
            name: Remove the EXTREMELY confusing unicode character U+2013
            language: system
            entry: perl -pi* -e 's/\xe2\x80\x93/-/g && ($t = 1) && print STDERR $_; END{{exit
                $t}}'
            files: ''

### Bash syntax validation

    -   repo: local
        hooks:
        -   id: check-bash-syntax
            name: Check Shell scripts syntax corectness
            language: system
            entry: bash -n
            files: \.sh$

### For Groovy-like Jenkins pipelines

```
-   repo: local
    hooks:
    -   id: forbid-abstract-classes-and-traits
        name: Ensure neither abstract classes nor traits are used
        language: pcre
        entry: "^(abstract|trait) "
        files: ^src/.*\.groovy$
```
**Rationale:** `abstract` classes & `traits` do not work in Jenkins pipelines : cf. https://issues.jenkins-ci.org/browse/JENKINS-39329 & https://issues.jenkins-ci.org/browse/JENKINS-46145

```
-   repo: local
    hooks:
    -   id: force-JsonSlurperClassic
        name: Ensure JsonSlurperClassic is used instead of non-serializable JsonSlurper
        language: pcre
        entry: JsonSlurper[^C]
        files: \.groovy$
```
**Rationale:** cf. http://stackoverflow.com/a/38439681/636849

```
-   repo: local
    hooks:
        -   id: Jenkinsfile-linter
            name: Check Jenkinsfile following the scripted-pipeline syntax using Jenkins API
            files: Jenkinsfile
            language: system
            entry: sh -c '! curl --silent $JENKINS_URL/job/MyPipelineName/job/master/1/replay/checkScriptCompile --user $JENKINS_USER:$JENKINS_TOKEN --data-urlencode value@Jenkinsfile | grep -F "\"status\":\"fail\""'
```
Note: the `$JENKINS_TOKEN` can be retrieved from `$JENKINS_URL/user/$USER_NAME/configure`

Beware, in 1 case on 6 I faced this unsolved bug with explictely-loaded libraries: https://issues.jenkins-ci.org/browse/JENKINS-42730

Also, there is also a linter for the declarative syntax: https://jenkins.io/doc/book/pipeline/development/#linter

### Forbid some Javascript keywords for browser retrocompatibility issues

    -   repo: local
        hooks:
        -   id: js-forbid-const
            name: The const keyword is not supported by IE10
            language: pcre
            entry: "const "
            files: \.js$
        -   id: js-forbid-let
            name: The let keyword is not supported by IE10
            language: pcre
            entry: "let "
            files: \.js$

### CSS

    -   repo: local
        hooks:
        -   id: css-forbid-px
            name: In CSS files, use rem or % over px
            language: pcre
            entry: px
            files: \.css$
        -   id: ot-sanitize-fonts
            name: Calling ot-sanitise on otf/ttf/woff/woff2 font files
            language: system
            entry: sh -c 'type ot-sanitise >/dev/null && for font in "$@"; do echo "$font"; ot-sanitise "$font"; done || echo "WARNING Command ot-sanitise not found - skipping check"'
            files: \.(otf|ttf|woff|woff2)$

### Some Angular 1.5 checks

    -   repo: local
        hooks:
        -   id: angular-forbid-apply
            name: In AngularJS, use $digest over $apply
            language: pcre
            entry: \$apply
            files: \.js$
        -   id: angular-forbid-ngrepeat-without-trackby
            name: In AngularJS, ALWAYS use 'track by' with ng-repeat
            language: pcre
            entry: ng-repeat(?!.*track by)
            files: \.html$
        -   id: angular-forbid-ngmodel-with-no-dot
            name: In AngularJS, "Whenever you have ng-model there's gotta be a dot in
                there somewhere"
            language: pcre
            entry: ng-model="?[^.]+[" ]
            files: \.html$
