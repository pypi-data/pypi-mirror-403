#!/bin/bash

source docker/common.env

USER_ID=$(id -u)
export USER_ID

set -ex

exec docker compose "$@"
