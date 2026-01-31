#! /usr/bin/env bash

function bluer_ai_git_push() {
    local message=$1
    if [[ -z "$message" ]]; then
        bluer_ai_log_error "@git: push: message not found."
        return 1
    fi

    local do_offline=$(bluer_ai_not $BLUER_AI_WEB_IS_ACCESSIBLE)
    local do_test=0

    if [[ -f "./.git-no-test" ]]; then
        bluer_ai_log "git tests are disabled by default."
        do_test=0
    fi

    local options=$2
    local do_browse=$(bluer_ai_option_int "$options" browse 0)
    local do_increment_version=$(bluer_ai_option_int "$options" increment_version 1)
    do_offline=$(bluer_ai_option_int "$options" offline $do_offline)
    local show_status=$(bluer_ai_option_int "$options" status 1)
    local first_push=$(bluer_ai_option_int "$options" first 0)
    local create_pull_request=$(bluer_ai_option_int "$options" create_pull_request $first_push)
    local do_action=$(bluer_ai_option_int "$options" action 1)
    local do_scp=$(bluer_ai_option_int "$options" scp 0)
    do_test=$(bluer_ai_option_int "$options" test $do_test)
    local run_workflows=$(bluer_ai_option_int "$options" workflow 1)

    if [[ "$do_scp" == 1 ]]; then
        local machine_name=$(bluer_ai_option "$options" rpi)
        if [[ -z "$machine_name" ]]; then
            bluer_ai_log_error "machine name not found."
            return 1
        fi
    fi

    [[ "$do_offline" == 1 ]] &&
        bluer_ai_log "⛓️‍💥 offline mode."

    if [[ "$do_increment_version" == 1 ]]; then
        bluer_ai_git_increment_version
        [[ $? -ne 0 ]] && return 1
    fi

    [[ "$show_status" == 1 ]] &&
        git status

    local repo_name=$(bluer_ai_git_get_repo_name)
    local plugin_name=$(bluer_ai_plugin_name_from_repo $repo_name)

    if [[ "$do_test" == 1 ]]; then
        bluer_ai_pylint \
            plugin=$plugin_name
        [[ $? -ne 0 ]] && return 1

        bluer_ai_pytest \
            plugin=$plugin_name
        [[ $? -ne 0 ]] && return 1

        bluer_ai_test \
            plugin=$plugin_name
        [[ $? -ne 0 ]] && return 1
    fi

    if [[ "$do_action" == 1 ]]; then
        bluer_ai_perform_action \
            action=git_before_push,plugin=$plugin_name
        if [[ $? -ne 0 ]]; then
            bluer_ai_log_error "@git: push: action failed."
            return 1
        fi
    fi

    git add .
    [[ $? -ne 0 ]] && return 1

    [[ "$run_workflows" == 0 ]] &&
        message="$message - no-workflow 🪄"

    git commit -a -m "$message"
    [[ $? -ne 0 ]] && return 1

    local extra_args=""
    [[ "$first_push" == 1 ]] &&
        extra_args="--set-upstream origin $(bluer_ai_git get_branch)"

    if [[ "$do_offline" == 0 ]]; then
        git push $extra_args
        [[ $? -ne 0 ]] && return 1

        if [[ "$create_pull_request" == 1 ]]; then
            bluer_ai_git create_pull_request
            [[ $? -ne 0 ]] && return 1
        fi

        [[ "$do_browse" == 1 ]] &&
            bluer_ai_git_browse . actions
    fi

    if [[ "$do_scp" == 1 ]]; then
        if [[ ! -d ".git" ]]; then
            bluer_ai_log_error "not a git repo."
            return 1
        fi

        local repo_name=$(basename $(pwd))
        bluer_ai_log "scp $repo_name -> $machine_name ..."

        bluer_ai_eval - \
            scp -r \
            ./ \
            pi@$machine_name.local:/home/pi/git/$repo_name
        [[ $? -ne 0 ]] && return 1
    fi

    local build_options=$3
    if [[ $(bluer_ai_option_int "$build_options" build 0) == 1 ]]; then
        bluer_ai_pypi_build $build_options,plugin=$plugin_name
    fi
}
