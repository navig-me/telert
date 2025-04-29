# Manual Tasks for Telert Project

## GitHub Action Publication

To publish the GitHub Action to the marketplace:

1. Push the changes to GitHub
2. Create a new release with tag `v1` or `v1.0.0`
3. Go to the GitHub repository
4. Click on the "Actions" tab 
5. Find the "Telert Run" action
6. Click "Draft a release" or "Publish this Action to the GitHub Marketplace"
7. Fill out required information:
   - Primary category (e.g., "Utilities")
   - Verification information
   - Release information

## VS Code Extension Publication

To publish the VS Code extension to the marketplace:

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
   npm init
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

## Docker Image Publication

To publish the Docker image to GitHub Container Registry:

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
   docker tag ghcr.io/navig-me/telert:latest ghcr.io/navig-me/telert:v0.1.25
   docker push ghcr.io/navig-me/telert:v0.1.25
   ```

5. Make the package public by going to the GitHub repository settings