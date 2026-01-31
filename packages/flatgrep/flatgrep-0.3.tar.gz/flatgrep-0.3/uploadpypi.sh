#!/usr/bin/env bash

echo "uploading to pypi"
uv run twine upload dist/*
