.PHONY: setup install clean vscode

# Create and activate env, install dependencies
it:
	pip install uv
	uv venv .venv
	# Using bash to source and run commands in one line
	. .venv/bin/activate && uv pip install --requirements pyproject.toml
	# Set the default Python interpreter for VSCode
	make vscode

# Install deps only
install:
	uv pip install --requirements pyproject.toml

# Remove virtual env
clean:
	rm -rf .venv

# Create or modify VSCode settings to use the .venv Python interpreter
vscode:
	@echo "Setting up VSCode Python interpreter..."
	# Create .vscode/settings.json if it doesn't exist and add the interpreter path
	mkdir -p .vscode
	echo '{ "python.defaultInterpreterPath": ".venv/bin/python" }' > .vscode/settings.json
