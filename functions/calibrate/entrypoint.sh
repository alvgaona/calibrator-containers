#!/bin/bash

source /shell-hook.sh

python -m awslambdaric lambda_function.handler
