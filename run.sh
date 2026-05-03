#!/bin/bash

DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -d "$DIR/.lvenv" ]; then
    . "$DIR/.lvenv/bin/activate"
    bash "$DIR/launch.sh"
elif [ -d "$DIR/.venv" ]; then
    . "$DIR/.venv/bin/activate"
    bash "$DIR/launch.sh"
else
    echo "The venv names don't match; check if you have a .venv / .lvenv folder or edit the script."
fi