# Initialize and update all submodules recursively
echo "Initializing and updating submodules..."
git submodule update --init --recursive

# Navigate to the Linking_tool submodule and install it
if [ -f models/Linking_tool/setup.py ]; then
    echo "Installing packages from setup.py..."
    pip install -e models/RESource
    pip install -e models/BC_Nexus
    pip install -e models/PyPSA_BC

else
    echo "setup.py not found in Linking_tool. Skipping installation."
fi

echo "Submodules initialized and packages installed successfully."
git submodule status