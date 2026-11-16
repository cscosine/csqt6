free_disk_script = r"""
set -euo pipefail

# Show available space
df -h

# Remove unnecessary tools/packages (do not fail if they are not installed)
sudo apt-get remove -y '^ghc-8.*' '^dotnet-.*' '^mongodb.*' 'mysql-.*' 'php.*' 'powershell' 'snap.*' || true
sudo apt-get autoremove -y
sudo apt-get clean

# Remove large directories
sudo rm -rf /usr/local/lib/android || true
sudo rm -rf /opt/hostedtoolcache || true

# Show available space
df -h
"""

free_disk_script_macos = r"""
set -euo pipefail

# Show available space
df -h /

# Android SDK, the Xcode versions other than the selected one, the simulators (do not fail if they are missing)
sudo rm -rf "${ANDROID_HOME:-$HOME/Library/Android/sdk}" || true
SELECTED_XCODE=$(xcode-select -p | sed 's|/Contents/Developer$||')
echo "Selected Xcode: ${SELECTED_XCODE}"
for x in /Applications/Xcode*.app; do
    if [ "$(cd "$x" && pwd -P)" != "$(cd "${SELECTED_XCODE}" && pwd -P)" ]; then
        sudo rm -rf "$x" || true
    fi
done
xcrun simctl delete all || true
sudo rm -rf "$HOME/Library/Developer/CoreSimulator" || true

# Show available space
df -h /
"""

#######################################################3


def init_repo_script_linux(repo_name: str) -> str:
    return rf"""
    set -euo pipefail

    cd workspace/{repo_name}
    ./init-repository
    """


def init_repo_script_windows(repo_name: str) -> str:
    return rf"""
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'

    cd workspace/{repo_name}
    ./init-repository.bat
    """


#######################################################3


# the configure options of every build (Linux, macOS, Windows)
# -no-feature-sql-mysql -no-feature-sql-psql: the MySQL and PostgreSQL drivers would link the client libraries the
# runner happens to have (libmysqlclient, libpq), not installed by the build nor by the consumers: not built.
# SQLite (built in) and ODBC (Windows: system) remain.
QT_CONFIGURE_OPTIONS = "-no-pch -skip qtwebengine -no-feature-sql-mysql -no-feature-sql-psql -release"


def configure_repo_script_linux(repo_name: str, extra_cmake_args: str = "") -> str:
    return rf"""
    set -euo pipefail

    ROOT_FOLDER=$(pwd)

    FOLDER_NAME="$CS_DIR_FROM_MATRIX"
    : "${{FOLDER_NAME:?missing FOLDER_NAME}}"

    REPO_FOLDER="${{ROOT_FOLDER}}/workspace/{repo_name}"
    BUILD_FOLDER="${{ROOT_FOLDER}}/workspace/build/${{FOLDER_NAME}}/{repo_name}/release"
    INSTALL_FOLDER="${{ROOT_FOLDER}}/workspace/install/${{FOLDER_NAME}}/{repo_name}"

    mkdir -p "${{INSTALL_FOLDER}}"
    mkdir -p "${{BUILD_FOLDER}}"

    cd "${{BUILD_FOLDER}}"

    "${{REPO_FOLDER}}/configure" {QT_CONFIGURE_OPTIONS} -prefix "${{INSTALL_FOLDER}}" {extra_cmake_args}
    """


def configure_repo_script_windows(repo_name: str) -> str:

    return rf"""
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'

    if (!(Test-Path ".venv")) {{
        python -m venv .venv
    }}
    & ".\.venv\Scripts\Activate.ps1"
    python -m pip install --upgrade pip
    pip install html5lib

    $ROOT_FOLDER = Get-Location

    $FOLDER_NAME = "$CS_DIR_FROM_MATRIX"
    $BUILD_FOLDER_NAME = "build-$CS_MATRIX_EXEC_ID"

    $REPO_FOLDER="$ROOT_FOLDER/workspace/{repo_name}"
    $BUILD_FOLDER="$ROOT_FOLDER/workspace/build/$BUILD_FOLDER_NAME/{repo_name}/release"
    $INSTALL_FOLDER="$ROOT_FOLDER/workspace/install/$FOLDER_NAME/{repo_name}"

    New-Item -ItemType Directory -Force -Path "$INSTALL_FOLDER" | Out-Null
    New-Item -ItemType Directory -Force -Path "$BUILD_FOLDER" | Out-Null

    Set-Location $BUILD_FOLDER

    & "$REPO_FOLDER/configure.bat" {QT_CONFIGURE_OPTIONS} -prefix "$INSTALL_FOLDER"
    if ($LASTEXITCODE) {{ exit $LASTEXITCODE }}
    """


# macOS: the oldest macOS the binaries run on, the minimum of Qt 6.11; explicit, so that it does not follow a newer Qt
MACOS_CONFIGURE_CMAKE_ARGS = "-- -DCMAKE_OSX_DEPLOYMENT_TARGET=13.0"


#######################################################3
def build_linux_script(repo_name: str) -> str:

    return rf"""
    set -euo pipefail

    ROOT_FOLDER=$(pwd)

    FOLDER_NAME="$CS_DIR_FROM_MATRIX"
    : "${{FOLDER_NAME:?missing FOLDER_NAME}}"

    BUILD_FOLDER="${{ROOT_FOLDER}}/workspace/build/${{FOLDER_NAME}}/{repo_name}/release"

    cd "${{BUILD_FOLDER}}"

    cmake --build .
    cmake --install .
    """


def build_windows_script(repo_name: str) -> str:

    return rf"""
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'

    $ROOT_FOLDER = Get-Location

    $BUILD_FOLDER_NAME = "build-$CS_MATRIX_EXEC_ID"

    $BUILD_FOLDER="$ROOT_FOLDER/workspace/build/$BUILD_FOLDER_NAME/{repo_name}/release"


    Set-Location $BUILD_FOLDER

    cmake --build .
    if ($LASTEXITCODE) {{ exit $LASTEXITCODE }}
    cmake --install .
    if ($LASTEXITCODE) {{ exit $LASTEXITCODE }}
    """


#######################################################
show_msvc_version_script = r"""
    Write-Host "=== Visual Studio ==="

    & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" `
        -latest `
        -products * `
        -property installationName

    & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" `
        -latest `
        -products * `
        -property catalog_productDisplayVersion

    Write-Host ""
    Write-Host "=== MSVC ==="

    $cl = Get-Command cl.exe -ErrorAction Stop

    Write-Host "cl.exe:"
    Write-Host $cl.Source
    """
