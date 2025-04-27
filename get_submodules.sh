# Initialize and update all submodules recursively
echo "Initializing and updating submodules..."
git submodule update --init --recursive

# Navigate to the submodule and install local packages
if [ -f models/Linking_tool/setup.py ]; then
    echo "Installing packages from submodules..."
    pip install -e models/RESource
    pip install -e models/osemosys_global
    pip install -e models/pypsa_eur


echo "Submodules initialized and packages installed successfully."
git submodule status