A few useful git hooks to integrate with [pre-commit](http://pre-commit.com).

Hooks that require Python dependencies, or specific to a language, have been extracted into separate repos:

- https://github.com/Lucas-C/pre-commit-hooks-bandit
- https://github.com/Lucas-C/pre-commit-hooks-go
- https://github.com/Lucas-C/pre-commit-hooks-html
- https://github.com/Lucas-C/pre-commit-hooks-lxml
- https://github.com/Lucas-C/pre-commit-hooks-nodejs
- https://github.com/Lucas-C/pre-commit-hooks-safety

## Usage

Check `.pre-commit-config.yaml` in this repo for usage examples and useful local hooks.

For the _remove-tabs_ hook, the number of whitespaces to substitute tabs with can be configured (it defaults to 4):

        args: [ --whitespaces-count, 2 ]

## Other useful local hooks

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
