#! /usr/bin/env bash

function test_bluer_ai_web_identify() {
    bluer_ai_web_identify
    [[ "$output" -ne 0 ]] &&
        return 1

    bluer_ai_hr

    bluer_ai_web_identify \
        loop,count=3,~upload
}
