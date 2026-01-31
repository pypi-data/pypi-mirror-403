#! /usr/bin/env bash

function bluer_ai_web_is_accessible() {
    url=$1
    if [[ -z "$url" ]]; then
        bluer_ai_log_error "url not found."
        return 1
    fi

    python3 -m bluer_ai.plugins.web \
        is_accessible \
        --url $url \
        "${@:2}"
}

bluer_ai_web_identify
