#!/bin/bash

# ---
# This script creates a Python virtual environment using uv
# and installs a specific git tag or branch from a repository into it.
# Usage: ./deploy_imsi_env.sh [python_version] [tag_or_branch] [deploy_path]
# Defaults are taken from environment variables if arguments are not provided.
# ---

# 1. Parse command line arguments or fall back to environment variables
PYTHON_VER="${1:-${IMSI_DEPLOYED_PYTHON_VER}}"
TAG_OR_BRANCH="${2:-${CI_COMMIT_TAG}}"
DEPLOY_PATH="${3:-${IMSI_DEPLOY_PATH}}"
REF_REPOS="${4:-${CANESM_REF_REPO}}"

# 2. Generate the environment name based on variables and the current date
CURRENT_DATE=$(date +%Y-%m-%d)
ENV_NAME="pyenv_${PYTHON_VER}_imsi_${TAG_OR_BRANCH}_${CURRENT_DATE}"
VENV_PATH="${DEPLOY_PATH}/${ENV_NAME}"
REALDIR="$(realpath "${CI_JOB_RUN_DIR}")"

# 3. Create the virtual environment
echo "Creating Python ${PYTHON_VER} environment named '${DEPLOY_PATH}/${ENV_NAME}'..."
${UV_BINARY} venv "${VENV_PATH}" --python "${PYTHON_VER}"

# 4. Activate the virtual environment
echo "Activating the virtual environment at ${VENV_PATH}"
source "${VENV_PATH}/bin/activate"

# 5. Install the package directly from the correct checkout done in the CI before_script
echo "Installing '${TAG_OR_BRANCH}' from '${REALDIR}'..."
${UV_BINARY} pip install --force-reinstall --no-cache-dir "file://${REALDIR}"

# 6. Run the post install script
${VENV_PATH}/bin/imsi-post-install --path-to-site-repos="${REF_REPOS}"

# 7. Softlink the new environment to 'latest'
ln -sfn "${VENV_PATH}" "${DEPLOY_PATH}/latest"

# 8. Print success message
echo ""
echo "✅ Setup complete."
echo "To activate the new environment, run:"
echo "source ${VENV_PATH}/bin/activate"
