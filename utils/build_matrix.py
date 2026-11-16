from csorchestrator.domain.context.context_compiler_generator import (
    Compiler,
    ContextCompilerGenerator,
    GeneratorWithType,
)
from csorchestrator.domain.context.context_os_architecture import (
    ARCHITECTURE_VARIANT_GENERIC,
    OS,
    Architecture,
    ContextOsArchitecture,
)
from csorchestrator.domain.context.context_os_architecture_compiler_generator import (
    ContextOsArchitectureCompilerGenerator,
)
from csorchestrator.frontend.cscmake_presets.supported_variants import (
    get_all_supported_os_version_list,
    get_supported_os_version_list,
)


def populate_build_matrix() -> list[ContextOsArchitectureCompilerGenerator]:
    ret_list: list[ContextOsArchitectureCompilerGenerator] = []

    ## LINUX. use multi-config for x64 arch, use single config for arm64 arch
    # every supported Ubuntu version: 22.04, 24.04, 26.04
    for os_version in get_all_supported_os_version_list(OS.LINUX):
        for arch in [Architecture.X64, Architecture.ARM64]:
            os_arch = ContextOsArchitecture(
                os=OS.LINUX,
                os_version=os_version,
                architecture=arch,
                architecture_variant=ARCHITECTURE_VARIANT_GENERIC,
            )
            generator = GeneratorWithType.NINJA
            compiler = Compiler.GCC

            ccg = ContextCompilerGenerator(
                compiler_family=compiler,
                compiler_version=ContextCompilerGenerator.COMPILER_VERSION_DEFAULT,
                build_generator=generator,
            )
            ret_list.append(
                ContextOsArchitectureCompilerGenerator(context_os_architecture=os_arch, context_compiler_generator=ccg)
            )

    ## WINDOWS, need to use ninja generator on msvc 2022
    for os_version in get_supported_os_version_list(OS.WINDOWS):
        os_arch = ContextOsArchitecture(
            os=OS.WINDOWS,
            os_version=os_version,
            architecture=Architecture.X64,
            architecture_variant=ARCHITECTURE_VARIANT_GENERIC,
        )

        generator = GeneratorWithType.NINJA
        compiler = Compiler.MSVC
        version = ContextCompilerGenerator.COMPILER_VERSION_MSVC_2022_17

        ccg = ContextCompilerGenerator(
            compiler_family=compiler,
            compiler_version=version,
            build_generator=generator,
        )
        ret_list.append(
            ContextOsArchitectureCompilerGenerator(context_os_architecture=os_arch, context_compiler_generator=ccg)
        )

    ## MACOS: arm64 (Apple Silicon), Apple Clang, Ninja (Qt configure builds the Release config only); both macOS
    ## versions, so that the archives stay available when the macos-15 runners are retired
    for os_version in get_all_supported_os_version_list(OS.MACOS):
        os_arch = ContextOsArchitecture(
            os=OS.MACOS,
            os_version=os_version,
            architecture=Architecture.ARM64,
            architecture_variant=ARCHITECTURE_VARIANT_GENERIC,
        )
        ccg = ContextCompilerGenerator(
            compiler_family=Compiler.APPLE_CLANG,
            compiler_version=ContextCompilerGenerator.COMPILER_VERSION_DEFAULT,
            build_generator=GeneratorWithType.NINJA,
        )
        ret_list.append(
            ContextOsArchitectureCompilerGenerator(context_os_architecture=os_arch, context_compiler_generator=ccg)
        )

    return ret_list
