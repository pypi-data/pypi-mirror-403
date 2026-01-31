#! /usr/bin/env bash

function bluer_ai_watch() {
    local options=$1
    local do_clear=$(bluer_ai_option_int "$options" clear 1)
    local count=$(bluer_ai_option "$options" count -1)

    local loop_count=0
    while true; do
        [[ "$do_clear" == 1 ]] && clear

        bluer_ai_eval "$@"

        loop_count=$((loop_count + 1))
        if [[ "$count" != -1 ]] &&
            [[ "$loop_count" -ge "$count" ]]; then
            break
        fi

        bluer_ai_sleep ,$options
    done
}
