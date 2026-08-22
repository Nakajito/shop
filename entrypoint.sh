#!/bin/sh
set -e

# Starts as root so it can fix the persistent media volume's ownership,
# then drops to the unprivileged appuser before running the real command.
#
# Why this exists: /app/media is a Coolify-managed volume mounted at
# container start, not part of the image — so the build-time
# `chown -R appuser:appuser /app` in the Dockerfile never touches it. If the
# volume was ever populated while the container ran as root (true for any
# volume that predates the non-root Dockerfile change), appuser can't write
# to it and every media upload fails silently from the user's perspective
# (see SECURITY.md). Reconciling ownership here, every boot, makes that
# self-healing instead of a one-time manual `chown` someone has to remember.
if [ -d /app/media ]; then
    chown -R appuser:appuser /app/media
fi

exec gosu appuser "$@"
