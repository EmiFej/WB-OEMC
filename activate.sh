#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Get the prompt name from UV's configuration (in case it's set)
ENV_NAME="WB-OEMC"

# Ensure the prompt shows the custom environment name
export PS1="($ENV_NAME)$PS1"

# Run any command after activating the environment
# For example, running Python
python --version
