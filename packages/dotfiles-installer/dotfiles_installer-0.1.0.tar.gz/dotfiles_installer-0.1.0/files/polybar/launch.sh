#!/usr/bin/env bash

THEME="minimal"

killall polybar
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

CONFIG_DIR=$(dirname $0)/themes/$THEME/config.ini

for m in $(polybar --list-monitors | cut -d ":" -f1); do
    export MONITOR=$m
    polybar -c $CONFIG_DIR &
done
