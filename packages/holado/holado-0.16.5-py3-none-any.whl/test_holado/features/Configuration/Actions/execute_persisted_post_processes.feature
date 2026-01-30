@configuration
@execute_persisted_post_processes
Feature: Execute persisted post processes
# Note: scenario post processes are executed before session post processes since it is the usual order of execution

    @scenario_post_processes
    Scenario: Execute persisted post processes at scenario level
        When execute persisted post processes of scenario context

    @session_post_processes
    Scenario: Execute persisted post processes at session level
        When execute persisted post processes of session context

