// SKIP LICENSE INSERTION
import static groovy.json.JsonOutput.*
import groovy.json.JsonSlurperClassic
import com.cloudbees.groovy.cps.NonCPS

def toto(Map args) {
    echo prettyPrint(toJson(args))
}
