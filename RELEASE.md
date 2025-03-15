# How to Create a Release

To create a new release of CryptoHub:

1. Make sure all your changes are committed and pushed to the main branch
2. Create a new tag for the version you want to release:

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. The GitHub Actions workflow will automatically:
   - Build the executable using PyInstaller with your main.spec file
   - Create a new GitHub release with the tag name
   - Upload cryptohub.exe as a release asset

4. You can check the progress in the "Actions" tab of your GitHub repository
5. Once completed, the release will be available in the "Releases" section of your repository

## Manual Release Process

If you prefer to build and release manually:

1. Build the executable:

   ```bash
   pyinstaller main.spec
   ```

2. Go to your GitHub repository and click on "Releases"
3. Click "Draft a new release"
4. Enter your tag version (e.g., v1.0.0)
5. Upload the `dist/cryptohub.exe` file
6. Publish the release
