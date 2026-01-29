#!/usr/bin/env bash

pkg="docp_core"
dirs="./build ./dist ./${pkg}.egg-info"

# Notification.
printf "\n| --- Building %s --- |\n" $pkg

# Check for existing build/dist directories.
printf "\nChecking for existing build directories ...\n\n"
for d in ${dirs}; do
    # Delete the directory if it exists.
    if [ -d "${d}" ]; then
        printf "|-- Deleting %s\n" ${d}
        rm -rf "${d}"
    fi
done

# Update requirements file.
printf "Updating the requirements file, ignoring './tests' ...\n"
preqs . --replace --ignore_dirs tests

# Initialise the config file.
read -p "Initialise (generalise) config.toml? (y|N): " resp
case "$resp" in
    y|Y)
        printf "|-- Initialising config.toml ...\n"
        sed 's/^docling = ".*"/docling = "<EMPTY>"/' -i ./docp_core/config/config.toml
        printf "|-- Done.\n\n"
        ;;
    *)
        printf "|-- Skipping.\n\n";;
esac

# Create the package and wheel file.
printf "\nCreating the source distribution ...\n"
python -m build --sdist --wheel --no-isolation

# Notfication.
printf "\nAll done.\n\n"

