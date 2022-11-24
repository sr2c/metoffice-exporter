SHELL := /bin/bash

export README_TEMPLATE_FILE ?= build-harness-extensions/templates/README.md.gotmpl

-include $(shell curl -sSL -o .build-harness "https://cloudposse.tools/build-harness"; echo .build-harness)
