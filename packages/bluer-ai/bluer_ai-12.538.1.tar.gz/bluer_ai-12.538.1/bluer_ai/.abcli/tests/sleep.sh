#! /usr/bin/env bash

function test_bluer_ai_sleep() {
    bluer_ai_sleep seconds=1.0
    [[ $? -ne 0 ]] && return 1

    bluer_ai_sleep ~log,seconds=1.0
}
