@testing_solution
@host_controller
Feature: Test Host Controller client

    Scenario: List containers

        Given CLIENT = new Host Controller client
            | Name  | Value                    |
            | 'url' | 'http://localhost:51231' |

        Given RESULT = list containers (Host Controller client: CLIENT)
        
        