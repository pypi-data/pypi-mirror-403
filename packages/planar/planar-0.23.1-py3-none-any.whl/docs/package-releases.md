# Package Releases and Installation

This document outlines the automated process for creating package releases and hosting them on a PEP 503 compliant index using GitHub Actions and GitHub Pages. It also provides instructions on how to install the package using this index.

## Automated Release Process

The release process is automated through two GitHub Actions workflows:

1.  **Create GitHub Release (`.github/workflows/create-release.yml`)**:
    *   **Triggers**:
        *   **Tag Push**: Automatically on a new tag matching `v[0-9]+.[0-9]+.[0-9]+*`.
        *   **Manual Dispatch**: Manually via the GitHub Actions UI, requiring a `branch` name as input.
    *   **Steps**:
        1.  **Determine Version**:
            *   For a tag push, the version is the tag name (e.g., `v1.2.3`).
            *   For a manual run, a development version is created, like `v0.0.0+my-branch`, based on the input branch.
        2.  **Checkout repository**: Checks out the code from the tag or the specified branch.
        3.  **Setup Python and uv**: Configures the necessary Python environment and installs `uv`.
        4.  **Build binary wheel**:
            *   Sets the package version using `uv version`.
            *   Builds the package wheel using `uv build --wheel`.
        5.  **Create GitHub Release**:
            *   Uses `gh release create` to create a new GitHub Release with the determined version as the tag.
            *   Development builds and tags with suffixes (e.g., `-alpha`) are marked as pre-releases.
            *   The built wheel (`dist/*.whl`) is uploaded as a release asset.
        6.  **Trigger Publish PyPI Pages workflow**:
            *   After successfully creating the release, it triggers the `publish-pypi-pages.yml` workflow to update the PEP 503 index.

2.  **Publish PyPI Index to GitHub Pages (`.github/workflows/publish-pypi-pages.yml`)**:
    *   **Triggers**:
        *   Automatically when a new release is published (triggered by the `create-release.yml` workflow).
        *   Manually via `workflow_dispatch`.
    *   **Permissions**:
        *   `contents: read`: To checkout the repository and download release assets.
        *   `pages: write`: To deploy to GitHub Pages.
        *   `id-token: write`: For OIDC authentication if needed (though not explicitly used for publishing in this setup).
    *   **Steps**:
        1.  **Checkout repository**: Checks out the code.
        2.  **Setup Python and uv**: Configures the Python environment and installs `uv`.
        3.  **Setup Pages**: Configures GitHub Pages for deployment.
        4.  **Prepare Pages Directory Structure**: Creates `gh-pages-content` (for the final site) and `temp_assets` (for downloaded release assets).
        5.  **Download the last 10 releases**:
            *   Uses `gh release list` and `gh release download` to fetch the assets (wheels) from the last 10 GitHub releases into the `temp_assets` directory.
        6.  **Generate PEP 503 Simple Index**:
            *   Runs a Python script (`scripts/generate_pypi_index.py`) that takes the downloaded assets from `temp_assets` and generates a PEP 503 compliant simple index in the `gh-pages-content` directory.
        7.  **Upload Pages artifact**: Uploads the `gh-pages-content` directory as a GitHub Pages artifact.
        8.  **Deploy to GitHub Pages**: Deploys the uploaded artifact to GitHub Pages, making the simple index available.

## Installing the Package

Once the releases are published to the GitHub Pages index, you can install the `planar` package using `uv` or `pip` by specifying the custom index URL.

### Installing a Stable Release

To install the latest stable version:

```bash
uv add planar --index=https://coplane.github.io/planar/simple/
```

Alternatively, if you want to use `pip`:

```bash
pip install planar --index=https://coplane.github.io/planar/simple/
```
This command tells `uv` (or `pip`) to look for the `planar` package at the specified index.

### Installing a Development Build

Development builds are created from branches and are marked as pre-releases. To install a specific development build (e.g., from the `feature/new-stuff` branch, which would have a version like `v0.0.0+feature-new-stuff`), you need to specify the exact version.

With `uv`:
```bash
uv add planar==v0.0.0+feature-new-stuff --index=https://coplane.github.io/planar/simple/
```

With `pip`:
```bash
pip install planar==v0.0.0+feature-new-stuff --index=https://coplane.github.io/planar/simple/
```
You can find the available versions in the "Releases" section of the GitHub repository.

### Optional dependencies

Planar has an optional integration with Otel collector. To install planar with the necessary libraries, use: 

```bash
pip install planar[otel] --index=https://coplane.github.io/planar/simple/
```
