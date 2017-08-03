A few useful git hooks to integrate with [pre-commit](http://pre-commit.com).

Hooks that require Python dependencies have been extracted into separate repos:

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
```
-   id: Jenkinsfile-linter
    name: Check Jenkinsfile following the scripted-pipeline syntax using Jenkins API
    files: Jenkinsfile
    language: system
    entry: sh -c '! curl --silent $JENKINS_URL/job/MyPipelineName/job/master/1/replay/checkScriptCompile --user $JENKINS_USER:$JENKINS_TOKEN --data-urlencode value@Jenkinsfile | grep -F "\"status\":\"fail\""'
```
Note: the `$JENKINS_TOKEN` can be retrieved from `$JENKINS_URL/user/$USER_NAME/configure`

Also, there is also a linter for the declarative syntax: https://jenkins.io/doc/book/pipeline/development/#linter
