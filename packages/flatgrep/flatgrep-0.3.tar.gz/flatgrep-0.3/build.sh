#!/usr/bin/env bash

echo "building project..."
uv run python -m build

read -p "Do you want to upload to PyPi Remote Repo? (y/n): " answer

case "$answer" in

y | Y | yes | YES)
  echo "Uploading..."
  bash ./uploadpypi.sh
  ;;

n | N | no | NO)
  echo "Exiting..."
  ;;

esac
