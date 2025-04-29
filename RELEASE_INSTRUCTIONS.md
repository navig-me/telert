# Release Instructions for telert v0.1.27

## Creating the GitHub Release

1. Go to the GitHub repository: https://github.com/navig-me/telert
2. Click on "Releases" in the right sidebar
3. Click "Draft a new release"
4. Select the tag "v0.1.27" from the dropdown 
5. Set the release title to: "Version 0.1.27: New logo and improved Docker API"
6. Copy the content from RELEASE_NOTES.md into the description field
7. Click "Publish release"

This will trigger the GitHub Actions workflow to build and publish the package to PyPI.

## Publishing the GitHub Action

After creating the release:

1. Go to the GitHub repository
2. Click on the "Actions" tab
3. In the left sidebar, click on the action "Telert Run"
4. Click "Draft a release to the GitHub Marketplace" or "Publish this Action to the GitHub Marketplace"
5. Fill out the required information:
   - Primary category: "Continuous Integration" or "Utilities"
   - Verification information: Your contact details
   - Release information: Details about how the action works

## Publishing the Docker Image

1. Log in to the GitHub Container Registry:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin
   ```

2. Build the Docker image:
   ```bash
   docker build -t ghcr.io/navig-me/telert:latest .
   ```

3. Push the image to GitHub Container Registry:
   ```bash
   docker push ghcr.io/navig-me/telert:latest
   ```

4. Tag with version number:
   ```bash
   docker tag ghcr.io/navig-me/telert:latest ghcr.io/navig-me/telert:v0.1.26
   docker push ghcr.io/navig-me/telert:v0.1.26
   ```

5. Make the package public by going to the GitHub repository settings

## Publishing the VS Code Extension

1. Install required tools:
   ```bash
   npm install -g @vscode/vsce
   ```

2. Navigate to the vscode-telert directory:
   ```bash
   cd vscode-telert
   ```

3. Run npm install to add required dependencies:
   ```bash
   npm init -y
   npm install --save-dev @types/vscode
   ```

4. Package the extension:
   ```bash
   vsce package
   ```

5. Publish to VS Code Marketplace:
   - Create a publisher on https://marketplace.visualstudio.com/
   - Generate a Personal Access Token in Azure DevOps
   - Run:
     ```bash
     vsce publish -p <your-access-token>
     ```

## Verifying the Release

After the release has been published, verify that:

1. The new version is available on PyPI: https://pypi.org/project/telert/
2. The GitHub Action is published in the GitHub Marketplace
3. The Docker image is available on GitHub Container Registry
4. The VS Code extension is published in the VS Code Marketplace