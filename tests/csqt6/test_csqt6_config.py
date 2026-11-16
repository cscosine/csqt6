from copy import deepcopy

import pytest
from csorchestrator.domain.context.context_compiler_generator import (
    Compiler,
    ContextCompilerGenerator,
    GeneratorWithType,
)
from csorchestrator.domain.context.context_os_architecture import OS
from csorchestrator.frontend.cscmake_presets.supported_variants import get_supported_context_os_architecture_list

from csqt6_config import qt6_mapping


def test_csorchestrator_config() -> None:

    all = get_supported_context_os_architecture_list()

    for config in all:
        res = qt6_mapping(deepcopy(config))  # deep copy to be sure
        assert res is not None

        if config.context_os_architecture.os == OS.LINUX:
            assert res.context_os_architecture == config.context_os_architecture
            assert res.context_compiler_generator == ContextCompilerGenerator(
                compiler_family=Compiler.GCC,
                compiler_version=ContextCompilerGenerator.COMPILER_VERSION_DEFAULT,
                build_generator=GeneratorWithType.NINJA,
            )
        elif config.context_os_architecture.os == OS.WINDOWS:
            assert res.context_compiler_generator == ContextCompilerGenerator(
                compiler_family=Compiler.MSVC,
                compiler_version=ContextCompilerGenerator.COMPILER_VERSION_MSVC_2022_17,
                build_generator=GeneratorWithType.NINJA,
            )
        else:
            raise AssertionError("non expected config")


def test_the_qt6_download_installs_the_system_packages_of_the_plugins(monkeypatch: pytest.MonkeyPatch) -> None:
    """With qt6 (or every library), the Ubuntu packages of the Qt plugins are installed before the download."""
    from pathlib import Path

    from csorchestrator.application.recipes.create_orchestrator import create_default_orchestrator
    from csorchestrator.foundation.core.report import Report
    from csorchestrator.frontend.step.step_custom_command import StepInstallAptPackages

    import csqt6_config

    monkeypatch.setattr(csqt6_config, "create_steps_to_get_libs_from_manifest", lambda **_: Report())

    def packages(required_libs: list[str] | None) -> list[list[str]]:
        o = create_default_orchestrator(name="consumer", version="1.0.0", base_install_dir=Path("install"))
        csqt6_config.auto_install_csorchestrator_managed_libraries(
            orchestrator=o,
            base_libs_dir=Path("libs"),
            manifest_description=None,  # type: ignore[arg-type]
            manifest_loaded=None,  # type: ignore[arg-type]
            dependencies_config_path=Path("dependencies"),
            mapping_function=lambda c: c,
            download_dependencies_manifest_and_bundle=True,
            phase_name_suffix="deps",
            required_libs=required_libs,
        )
        return [s.packages for p in o.phases for s in p.steps if isinstance(s, StepInstallAptPackages)]

    assert packages(["qt6"]) == [csqt6_config.QT6_PLUGINS_UBUNTU_PACKAGES]
    assert packages(None) == [csqt6_config.QT6_PLUGINS_UBUNTU_PACKAGES]
    assert packages([]) == []
