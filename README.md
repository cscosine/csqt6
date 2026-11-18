# csqt6

Automated cross-platform build system and CI pipeline recipe for **Qt 6** (targeting **v6.12.0**), powered by [**csorchestrator**](https://github.com/cscosine/csorchestrator).

---

## Getting Started

### Prerequisites

* Python `>= 3.11`
* Git
* [csorchestrator](https://github.com/cscosine/csorchestrator) cloned as a peer directory (`../csorchestrator`)

### Environment Setup

Bootstrap the local virtual environment, install dev dependencies, link `csorchestrator` in editable mode, and install git hooks:

**Linux / macOS:**
```bash
./setup.sh
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\setup.ps1
.\.venv\Scripts\Activate.ps1
```

### Running the Orchestrator Locally

Execute the orchestrator script to run pipeline steps locally:

```bash
./qt6_project.py
# or
python qt6_project.py
```

### Re-generating the GitHub Workflow

To re-generate the GitHub Actions CI workflow (`.github/workflows/csqt6.yml`) from the definition in [`csqt6_project.py`](csqt6_project.py):

```bash
./csqt6_project.py generate-github-workflow
# or
python csqt6_project.py generate-github-workflow
```

### Development & Quality Checks

Run linting, static type checking, and test suites:

```bash
# Code formatting and linting
ruff check .
ruff format .

# Strict type checking
python -m mypy . --config-file=pyproject.toml

# Unit tests
pytest

# Run all pre-commit hooks
pre-commit run --all-files
```

---

## Overview

Building Qt 6 from source across multiple platforms (Linux and Windows) and architectures (`x64` and `arm64`) can be complex and error-prone. **csqt6** defines a declarative build and packaging recipe in Python using the `csorchestrator` framework.

With this setup:
- The build pipeline, dependencies, and configuration flags are defined in Python code.
- Cross-platform CI workflows (e.g. [`.github/workflows/csqt6.yml`](.github/workflows/csqt6.yml)) are automatically generated.
- Build artifacts, manifests, and release archives (`.tar.gz` bundles) are assembled consistently across environments.

---

## Architecture & Build Pipeline

The core build recipe is defined in [`csqt6_project.py`](csqt6_project.py) and executed across the matrix defined in [`utils/build_matrix.py`](utils/build_matrix.py).

### Excluded Qt modules

Every module licensed under the GPL only (no LGPL option) is neither cloned nor built (`QT_EXCLUDED_MODULES` in
[`utils/scripts.py`](utils/scripts.py)), so the archives contain only LGPL / BSD libraries: Qt Charts, Data
Visualization, Graphs, Quick 3D, Quick 3D Physics, Quick Timeline, Quick Effect Maker, Lottie, Virtual Keyboard, Network
Authorization, CoAP, MQTT, HTTP Server, Canvas Painter, the translations, and the Wayland compositor
(`-no-feature-wayland-server`; the Wayland client remains). Qt WebEngine and Qt PDF are no longer part of the Qt release
since 6.12. The tools under the Qt GPL exception (Designer, qmllint, qsb, ...) remain: using them does not put the GPL
on the consumer.

macOS: the binaries run from macOS 14.4 (the minimum of Qt 6.12); a consumer of Qt sets at least this deployment
target.

### Version Alignment

The project version (`6.12.0`, tracking the Qt release being built) is defined as a single source of truth in [`csqt6/csorchestrator_config.py`](csqt6/csorchestrator_config.py) (`CSQT6_PROJECT_NAME` / `CSQT6_PROJECT_VERSION`), imported by [`csqt6_project.py`](csqt6_project.py) and mirrored in [`pyproject.toml`](pyproject.toml) — keep the two aligned when bumping the version.

### Execution Phases

1. **Repo Update**:
   - Performs a shallow clone (`depth=1`) of `qt/qt5.git` at tag `v6.12.0` into `workspace/qt6`.
2. **Install Requirements (Linux-Ubuntu)**:
   - Cleans disk space on CI runners to ensure sufficient storage for large Qt builds.
   - Installs system packages required for Qt 6 GUI, Wayland, X11/XCB, and font rendering (see [`utils/apt_packages_list.py`](utils/apt_packages_list.py)).
3. **Configure & Build (Linux-Ubuntu)**:
   - Runs `./init-repository --module-subset=default,-<module>...` inside the cloned Qt directory, without the excluded
     modules (`QT_EXCLUDED_MODULES` in [`utils/scripts.py`](utils/scripts.py)).
   - Configures Qt with `-no-pch -skip <module>... -no-feature-sql-mysql -no-feature-sql-psql -release
     -no-feature-wayland-server -prefix <INSTALL_FOLDER>`.

   - Compiles and installs Qt via `cmake --build .` and `cmake --install .`.
4. **Configure & Build (Windows)**:
   - Configures the MSVC developer environment using `setup-msvc-dev@v4`.
   - Verifies compiler versions (`vswhere.exe` and `cl.exe`).
   - Runs `init-repository.bat`.
   - Prepares a Python virtual environment with `html5lib`.
   - Configures and compiles Qt with MSVC and Ninja.
5. **Artifacts & Release Bundling**:
   - Packages build outputs into tarball archives.
   - Generates `.csOrchestratorManifest` metadata and release bundles (`csqt6-6.12.0-bundle.tar.gz`).

### Library Dependencies

Qt 6 is a **self-contained, single-source** build: the `qt6` repository has no compile/link-time dependencies on other csorchestrator-managed libraries, so `LIBRARY_DEPENDENCIES` in [`csqt6/csorchestrator_config.py`](csqt6/csorchestrator_config.py) is intentionally empty.

Downstream projects can consume a csqt6 GitHub release via the `auto_install_csorchestrator_managed_libraries()` helper in the same module: it downloads the release manifest, the `.tar.gz` bundle, and the requested libraries into `base_libs_dir` with minimal boilerplate (transitive dependency auto-fill is wired in via `LIBRARY_DEPENDENCIES` for future use).

---

## Supported Build Matrix

The target execution matrix is configured in [`utils/build_matrix.py`](utils/build_matrix.py):

| OS | Version | Architecture | Compiler | Generator |
|---|---|---|---|---|
| **Linux** | Ubuntu 22.04 | `x64` | GCC (default) | Ninja |
| **Linux** | Ubuntu 22.04 | `arm64` | GCC (default) | Ninja |
| **Linux** | Ubuntu 24.04 | `x64` | GCC (default) | Ninja |
| **Linux** | Ubuntu 24.04 | `arm64` | GCC (default) | Ninja |
| **Linux** | Ubuntu 26.04 | `x64` | GCC (default) | Ninja |
| **Linux** | Ubuntu 26.04 | `arm64` | GCC (default) | Ninja |
| **Windows** | Windows 10 | `x64` | MSVC 2022 (v17) | Ninja |
| **macOS** | macOS 15 | `arm64` | Apple Clang (Xcode) | Ninja |
| **macOS** | macOS 26 | `arm64` | Apple Clang (Xcode) | Ninja |

Toolchain mappings for each platform are provided in [`csqt6/csorchestrator_config.py`](csqt6/csorchestrator_config.py).

## Rebuilding Qt

The archives of the releases are Qt built **unmodified** from the official sources, with the options below
([`utils/scripts.py`](utils/scripts.py)). To build the same Qt by hand, e.g. a modified Qt to replace the one of an
application (the LGPL allows it, see below):

1. **Source**: Qt 6.12.0, the tag `v6.12.0` of `qt5.git` (<https://code.qt.io/qt/qt5.git>, mirrored at
   <https://github.com/qt/qt5>), without the GPL-only modules ([Excluded Qt modules](#excluded-qt-modules)):

   ```bash
   git clone --branch v6.12.0 --depth 1 https://github.com/qt/qt5.git qt6
   cd qt6
   ./init-repository --module-subset=default,-qtcharts,-qtdatavis3d,-qtgraphs,-qtquick3d,-qtquick3dphysics,-qtquicktimeline,-qtquickeffectmaker,-qtlottie,-qtvirtualkeyboard,-qtnetworkauth,-qtcoap,-qtmqtt,-qthttpserver,-qtcanvaspainter,-qttranslations
   ```

   (On Windows `init-repository.bat`.) The source archive `qt-everywhere-src-6.12.0` of
   <https://download.qt.io/official_releases/qt/6.12/6.12.0/> is the same code, with every module: the `-skip` options
   below leave the excluded ones out.

2. **Configure**, in an empty build folder, with the compiler of the platform: Linux, the GCC of the Ubuntu release
   (x64 or arm64; the packages of [`utils/apt_packages_list.py`](utils/apt_packages_list.py)); Windows, MSVC 2022 x64
   (an *x64 Native Tools* prompt, Python with `html5lib`); macOS, the Apple Clang of Xcode (arm64). Ninja and CMake
   on the `PATH`:

   ```bash
   <qt6>/configure -no-pch -skip qtcharts -skip qtdatavis3d -skip qtgraphs -skip qtquick3d -skip qtquick3dphysics -skip qtquicktimeline -skip qtquickeffectmaker -skip qtlottie -skip qtvirtualkeyboard -skip qtnetworkauth -skip qtcoap -skip qtmqtt -skip qthttpserver -skip qtcanvaspainter -skip qttranslations -no-feature-sql-mysql -no-feature-sql-psql -release -prefix <install folder> <platform options>
   ```

   (On Windows `configure.bat`.) The platform options: Linux `-no-feature-wayland-server` (the Wayland compositor is
   GPL only; the Wayland client remains); macOS `-- -DCMAKE_OSX_DEPLOYMENT_TARGET=14.4`; Windows none.

3. **Build and install**: `cmake --build .` then `cmake --install .`; `<install folder>` is then the same layout as the
   archives (`lib/`, `plugins/`, `bin/`, `sbom/`, ...).

`./csqt6_project.py` runs the whole recipe for the current platform (see
[Running the Orchestrator Locally](#running-the-orchestrator-locally)).

### Replacing Qt in an application

An application that ships Qt as shared libraries (e.g. a deployment made by csCMake `cs_deployment`) can run with
another build of Qt in place of its own, which the LGPL v3 of Qt allows:

- Qt **6.x, the same or a later release** than the one the application was built with (Qt keeps binary compatibility
  within Qt 6), built for the same platform (the compiler ABI of the table above, the architecture, an Ubuntu release
  not newer than the one of the application).
- **Every** Qt library and plugin of the application, from the same Qt build: the plugins must match the libraries.
- Copy them over the ones of the application: Linux `lib/libQt6*.so.6*` and `plugins/`; Windows `Qt6*.dll` and the
  plugin folders (`platforms/`, `styles/`, ...) next to the executable; macOS the frameworks of `lib/` and `plugins/`,
  then sign the application again (e.g. ad hoc: `codesign --force --deep --sign - <application folder>`).

The README of the application says which libraries and plugins it ships (e.g.
[csImgTracker](https://github.com/cscosine/csImgTracker#replacing-the-qt-libraries)).

### Licenses of the archives

The libraries and plugins of the archives are under the LGPL v3 (or the GPL v2/v3, or the commercial license of The Qt
Company), the GPL-only modules being excluded; the tools under the GPL with the Qt GPL exception. The third-party code
inside Qt, with its licenses and copyrights, is listed in the SBOM of every archive (`sbom/<repository>-6.12.0.spdx`,
SPDX); it differs per platform (on Windows and macOS Qt bundles HarfBuzz, FreeType, libpng, PCRE2, ...; on Linux it
uses the libraries of the system). An application shipping Qt ships these notices and the license texts (e.g.
csImgTracker `licenses/`, generated from the SBOM).

---

## Repository Structure

```
csqt6/
├── .agents/skills/
│   └── csqt6-orchestrator-recipe/  # Agent skill for auditing recipes & re-generating workflows
├── csqt6_project.py                          # Main orchestrator pipeline recipe (source of truth)
├── pyproject.toml                  # Project packaging, Ruff, MyPy, and Pytest configuration
├── setup.sh / setup.ps1            # Environment bootstrap scripts (Linux / Windows)
├── open-code.sh / open-code.ps1    # Helper scripts to launch VS Code inside the virtualenv
├── .pre-commit-config.yaml         # Pre-commit checks (Ruff, MyPy, Actionlint)
├── csqt6/
│   └── csorchestrator_config.py    # Toolchain and compiler mapping logic (included in release)
├── utils/
│   ├── build_matrix.py             # OS, architecture, and generator matrix definitions
│   ├── scripts.py                  # Bash and PowerShell script templates for build phases
│   └── apt_packages_list.py        # System package dependencies for Ubuntu
├── csorchestratorsdk/portable/     # [Autogenerated / Vendored] Standalone SDK synced from csorchestrator
├── tests/
│   └── csqt6/                      # Unit tests for configuration mappings
└── .github/workflows/
    └── csqt6.yml                     # [Autogenerated] GitHub Actions CI workflow (emitted by csqt6_project.py)
```

### Autogenerated Files Lifecycle

| Path | Origin / Trigger | Maintenance Policy |
|---|---|---|
| [`.github/workflows/csqt6.yml`](.github/workflows/csqt6.yml) | Autogenerated by running `./csqt6_project.py generate-github-workflow`. | **Never edit manually.** Edit `csqt6_project.py` or files in `utils/`, then re-run the generator command. |
| [`csorchestratorsdk/portable/`](csorchestratorsdk/portable/) | Autogenerated & exported by `csorchestrator`. | Synced from `csorchestrator` to provide lightweight release manifest utilities on CI runners without requiring `pip install csorchestrator`. |
| `workspace/` *(gitignored)* | Created at runtime when running `./csqt6_project.py` locally. | Holds cloned Qt sources (`workspace/qt6`), temporary build directories, and install outputs. Can be safely deleted to reset local state. |

---

## Agent Skills

This repository includes a project-specific agent skill under [`.agents/skills/`](.agents/skills/):

* [**`csqt6-orchestrator-recipe`**](.agents/skills/csqt6-orchestrator-recipe/SKILL.md): Guides AI coding assistants in auditing recipe consistency (checking that extra files exist, verifying version alignment, and validating script imports), re-generating the GitHub Actions workflow (`./csqt6_project.py generate-github-workflow`), and running pre-commit quality checks.

### How to Use the Skill

* **Automatic Activation (Natural Language)**: When using an AI coding assistant (e.g. Antigravity, Codex, Claude Code), the assistant automatically indexes `.agents/skills/` and follows this skill when given relevant prompts, such as:
  * *"Audit the csqt6_project recipe consistency"*
  * *"Update Qt version to v6.11.2 and re-generate the workflow"*
  * *"Add a new build target to the matrix and update CI"*
* **Explicit Invocation**: Prompt the assistant directly:
  * *"Use the `csqt6-orchestrator-recipe` skill to audit the build recipe"*
  * Or use the slash command `/csqt6-orchestrator-recipe` (if supported by your client)
* **Human Developer Runbook (Standard Operating Procedure / SOP)**: For manual work without an AI assistant, [`.agents/skills/csqt6-orchestrator-recipe/SKILL.md`](.agents/skills/csqt6-orchestrator-recipe/SKILL.md) serves as a concise checklist for extra files, version alignment, and workflow re-generation commands.

---

## TODO & Future Ideas

- [ ] **Compiler Caching (`ccache` on Linux / `sccache` on Windows)**:
  - Integrate compiler caching into CI via GitHub Actions caching (`actions/cache`).
  - *Mechanism & Trade-offs*: Even though CI runners start from scratch, `actions/cache` restores cached object files at the start of the job, allowing `ccache` to skip recompiling unchanged translation units. This can significantly speed up iterative runs on `main` and `dev` branches, though it must be monitored against GitHub's **10 GB repository cache quota** due to the size of Qt 6 builds.

---

## License

The scripts of this repository are licensed under the [MIT License](LICENSE). The Qt they build keeps its own
licenses: see [Licenses of the archives](#licenses-of-the-archives).
