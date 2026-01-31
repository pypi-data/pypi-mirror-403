#! /usr/bin/env bash

function test_bluer_sbc_camera_capture() {
    local current_path=$(pwd)

    [[ "$BLUER_SBC_SESSION_IMAGER_ENABLED" == 0 ]] &&
        return 0

    local options=$1

    bluer_ai_select \
        test_bluer_sbc_camera_capture-$(bluer_ai_string_timestamp_short)

    bluer_ai_eval ,$options \
        bluer_sbc_camera \
        capture \
        image
    [[ $? -ne 0 ]] && return 1

    cd $current_path
}

function test_bluer_sbc_camera_capture_video() {
    local current_path=$(pwd)

    [[ "$BLUER_SBC_SESSION_IMAGER_ENABLED" == 0 ]] ||
        [[ "$abcli_is_rpi" = false ]] &&
        return 0

    local options=$1

    bluer_ai_select \
        test_bluer_sbc_camera_capture_video-$(bluer_ai_string_timestamp_short)

    bluer_ai_eval ,$options \
        bluer_sbc_camera \
        capture \
        video \
        --length 3 \
        --preview 1
    [[ $? -ne 0 ]] && return 1

    cd $current_path
}

function test_bluer_sbc_camera_preview() {
    [[ "$BLUER_SBC_SESSION_IMAGER_ENABLED" == 0 ]] &&
        return 0

    local options=$1

    bluer_ai_eval ,$options \
        bluer_sbc_camera \
        preview \
        - \
        --length 3
}
