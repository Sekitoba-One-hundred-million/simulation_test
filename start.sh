#!/bin/bash

PIPSERVER='100.95.241.19'
pip install --extra-index-url http://"${PIPSERVER}" --trusted-host "${PIPSERVER}" -U SekitobaLibrary

python main.py
