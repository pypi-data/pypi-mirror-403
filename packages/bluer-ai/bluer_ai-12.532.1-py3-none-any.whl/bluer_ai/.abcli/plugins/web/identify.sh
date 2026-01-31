#! /usr/bin/env bash

function bluer_ai_web_identify() {
    local options=$1
    local do_loop=$(bluer_ai_option_int "$options" loop 0)

    local identification_options=$2

    if [[ "$do_loop" == 1 ]]; then
        bluer_ai_watch \
            ~clear,~log,seconds=5,$options \
            bluer_ai_web_identify \
            timestamp,$identification_options \
            "${@:3}"

        return
    fi

    local add_timestamp=$(bluer_ai_option_int "$options" timestamp 0)
    local do_log=$(bluer_ai_option_int "$options" log 1)

    export BLUER_AI_PYPI_IS_ACCESSIBLE=$(
        bluer_ai_web_is_accessible \
            https://pypi.org/ \
            "${@:2}"
    )
    export BLUER_AI_STORAGE_IS_ACCESSIBLE=$(
        bluer_ai_web_is_accessible \
            $BLUER_AI_STORAGE_CHECK_URL \
            "${@:2}"
    )
    export BLUER_AI_WEB_IS_ACCESSIBLE=$(
        bluer_ai_web_is_accessible \
            $BLUER_AI_WEB_CHECK_URL \
            "${@:2}"
    )

    if [[ "$do_log" == 1 ]]; then
        bluer_ai_log $(
            python3 -m bluer_options.web \
                access_as_str \
                --timestamp $add_timestamp
        )
    fi
}
