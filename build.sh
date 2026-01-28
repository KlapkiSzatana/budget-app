#!/bin/bash
python3 -m nuitka \
    --standalone \
    --enable-plugin=pyside6 \
    --include-data-dir=locales=locales \
    --include-data-file=budget.png=budget.png \
    --static-libpython=no \
    --output-dir=dist \
    --linux-icon=budget.png \
    budget-app.py
