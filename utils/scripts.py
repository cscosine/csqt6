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


# The modules not built (their sources not even cloned): the ones licensed under the GPL only
# (LicenseRef-Qt-Commercial OR GPL-3.0-only in their sources, no LGPL option; checked on Qt 6.11.3 and 6.12.0), so that
# every archive is LGPL / BSD and a consumer never links a GPL-only Qt library. (Qt WebEngine and Qt PDF are released
# apart since Qt 6.12.)
# The commercial-only Qt products (Qt for MCUs, Safe Renderer, Insight, ...) are not in qt5.git: nothing to exclude.
# Kept although GPL: the tools with the Qt GPL exception (designer, qmllint/qmlls, qsb, ...): their use and their
# output do not put the GPL on the consumer.
QT_EXCLUDED_MODULES = [
    "qtcharts",
    "qtdatavis3d",
    "qtgraphs",
    "qtquick3d",
    "qtquick3dphysics",
    "qtquicktimeline",
    "qtquickeffectmaker",
    "qtlottie",
    "qtvirtualkeyboard",
    "qtnetworkauth",
    "qtcoap",
    "qtmqtt",
    "qthttpserver",
    "qtcanvaspainter",
    "qttranslations",
]

QT_INIT_REPOSITORY_OPTIONS = "--module-subset=default," + ",".join(f"-{m}" for m in QT_EXCLUDED_MODULES)


def init_repo_script_linux(repo_name: str) -> str:
    return rf"""
    set -euo pipefail

    cd workspace/{repo_name}
    ./init-repository {QT_INIT_REPOSITORY_OPTIONS}
    """


def init_repo_script_windows(repo_name: str) -> str:
    return rf"""
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'

    cd workspace/{repo_name}
    ./init-repository.bat "{QT_INIT_REPOSITORY_OPTIONS}"
    if ($LASTEXITCODE) {{ exit $LASTEXITCODE }}
    """


#######################################################3


# the configure options of every build (Linux, macOS, Windows)
# -no-feature-sql-mysql -no-feature-sql-psql: the MySQL and PostgreSQL drivers would link the client libraries the
# runner happens to have (libmysqlclient, libpq), not installed by the build nor by the consumers: not built.
# SQLite (built in) and ODBC (Windows: system) remain.
# -skip: QT_EXCLUDED_MODULES, also at configure (in case a dependency brought one of them in at init-repository).
QT_CONFIGURE_OPTIONS = (
    "-no-pch "
    + " ".join(f"-skip {m}" for m in QT_EXCLUDED_MODULES)
    + " -no-feature-sql-mysql -no-feature-sql-psql -release"
)

# Linux: no Wayland compositor (Qt Wayland Compositor, GPL only; the Wayland client and its plugins remain)
LINUX_CONFIGURE_ARGS = "-no-feature-wayland-server"


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


# macOS: the oldest macOS the binaries run on, the minimum of Qt 6.12 (QT_SUPPORTED_MIN_MACOS_VERSION); explicit, so
# that it does not follow the macOS of the build machine. A consumer of Qt sets at least this value.
MACOS_CONFIGURE_CMAKE_ARGS = "-- -DCMAKE_OSX_DEPLOYMENT_TARGET=14.4"


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
