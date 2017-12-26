#!/bin/bash

VBoxClient-all &
setxkbmap -layout us,ru -variant ,winkeys -option grp:caps_toggle,grp_led:scroll &
kbdd &
dbus-update-activation-environment --systemd --all &
thunar --daemon &