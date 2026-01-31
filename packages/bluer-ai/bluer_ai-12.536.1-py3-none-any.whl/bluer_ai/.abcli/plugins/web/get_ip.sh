#! /usr/bin/env bash

function bluer_ai_web_get_ip_() {
    ifconfig | grep inet | grep -v inet6 | grep -v 127.0.0.1 | awk '{print $2}'
}

function bluer_ai_web_get_ip() {
    export BLUER_AI_IP=$(bluer_ai_web_get_ip_)
    bluer_ai_log "IP: $BLUER_AI_IP"
}
