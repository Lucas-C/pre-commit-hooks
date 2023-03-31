// TODO: This license is not consistent with the license used in the project.
//       Delete the inconsistent license and above line and rerun pre-commit to insert a good license.
// Copyright (C) 2017
// Teela O'Malley
//
// Licensed under the Apache License, Version 2.0 (the 'License');

import static groovy.json.JsonOutput.*
import groovy.json.JsonSlurperClassic
import com.cloudbees.groovy.cps.NonCPS

def toto(Map args) {
    echo prettyPrint(toJson(args))
}
