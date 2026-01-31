#! /usr/bin/env bash

function bluer_ai_sleep() {
    local options=$1
    local do_log=$(bluer_ai_option_int "$options" log 1)
    local seconds=$(bluer_ai_option "$options" seconds 3)

    [[ "$do_log" == 1 ]] &&
        bluer_ai_log_local "sleeping for $seconds s ... (^C to stop)"

    sleep $seconds
}
