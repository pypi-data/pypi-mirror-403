#! /usr/bin/env bash

function bluer_ai_web_diagnose() {
    local connection=$(bluer_ai_option "$options" Zagros,Sion $BLUER_AI_WIFI_SSID)

    bluer_ai_log "connection: $connection through $BLUER_AI_WIFI_SSID"

    if [[ "$connection" == "Sion" ]]; then
        bluer_ai_browse https://my.mci.ir/panel
        bluer_ai_browse http://192.168.0.1/settings.html#Advanced/Wireless/OnlineClients
    elif [[ "$connection" == "Zagros" ]]; then
        bluer_ai_browse http://router.miwifi.com/cgi-bin/luci/diagnosis
    else
        bluer_ai_log_warning "cannot diagnose connection: $connection."
    fi
}
