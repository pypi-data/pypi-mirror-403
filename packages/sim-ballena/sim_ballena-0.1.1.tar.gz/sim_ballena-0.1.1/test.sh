#!/bin/bash
# Archivo: test


if [[ "$1" == "build" ]]; then
    source .venv/bin/activate
    maturin develop
fi

.venv/bin/python3 test_file.py