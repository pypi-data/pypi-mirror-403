#! /usr/bin/env bash

function bluer_ai_web() {
    local task=${1:-share}

    local function_name=bluer_ai_web_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 -m bluer_ai.plugins.web "$@"
}

bluer_ai_source_caller_suffix_path /web
