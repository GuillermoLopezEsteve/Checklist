#!/bin/bash

REPO_DIR=~/Checklist
SETUP_SCRIPT=~/Checklist/setup.sh

while true; do
    echo "Press 'y' to check for updates (or 'q' to quit)..."
    read -n 1 -r key
    echo ""

    if [[ $key == "q" || $key == "Q" ]]; then
        echo "Exiting..."
        break
    fi

    if [[ $key == "y" || $key == "Y" ]]; then
        cd "$REPO_DIR" || { echo "Repo not found!"; continue; }

        # Check for local changes
        if [[ -n $(git status --porcelain) ]]; then
            echo "Local changes detected. Stashing..."
            git stash
        fi

        echo "Pulling latest changes..."
        OUTPUT=$(git pull)

        echo "$OUTPUT"

        # If git pull actually updated something
        if ! echo "$OUTPUT" | grep -q "Already up to date"; then
            echo "Changes detected. Running setup script..."
            sudo bash "$SETUP_SCRIPT"
        else
            echo "No updates found."
        fi
    fi
done
