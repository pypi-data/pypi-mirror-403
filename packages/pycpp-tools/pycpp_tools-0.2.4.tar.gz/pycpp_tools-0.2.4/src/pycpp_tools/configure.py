import os, re, shutil, platform
from enum import Enum
import pydantic
import subprocess
import sys


class Language(str, Enum):
    C = "C"
    CXX = "CXX"


class Generator(str, Enum):
    Ninja = "Ninja"
    VS2022 = "Visual Studio 17 2022"
    VS2019 = "Visual Studio 16 2019"
    VS2026 = "Visual Studio 18 2026"
    NMake = "NMake"
    Makefiles = "Makefiles"
    MinGWMakefiles = "MinGW Makefiles"


class Compiler(str, Enum):
    Clang = "Clang"
    MSVC = "MSVC"
    GCC = "GCC"
    LLVM_MINGW = "clang-llvm"


class BuildType(str, Enum):
    Debug = "Debug"
    Release = "Release"


class Architecture(str, Enum):
    x86 = "x86"
    x64 = "x64"
    arm64 = "arm64"


class TargetType(str, Enum):
    Executable = "Executable"
    StaticLibrary = "StaticLibrary"
    DynamicLibrary = "DynamicLibrary"
    PyBind11Module = "PyBind11Module"
    PyBind11SharedLibrary = "PyBind11SharedLibrary"


class LibType(str, Enum):
    Static = "Static"
    Dynamic = "Dynamic"
    HeaderOnly = "HeaderOnly"
    System = "System"


class LibSearchType(str, Enum):
    DIR = "DIR"
    ROOT = "ROOT"
    PREFIX_PATH = "PREFIX_PATH"


class PolicyType(str, Enum):
    NEW = "NEW"
    OLD = "OLD"


class Lib(pydantic.BaseModel):
    name: str = ""
    version: str = ""
    home: str = ""
    type: LibType = LibType.Dynamic
    search_type: LibSearchType = LibSearchType.DIR
    components: list[str] = []
    components_link: bool = True
    links: list[str] = []
    bin: list[str] = []
    include: list[str] = []
    vars: dict[str, str] = {}

    @property
    def include_dir(self):
        if len(self.include) > 0:
            return self.include.copy()
        return [f"${{{self.name}_INCLUDE_DIRS}}"]


class Target(pydantic.BaseModel):
    name: str = ""
    type: TargetType = TargetType.Executable
    src_files: list[str] = []
    include_dirs: list[str] = []
    compile_options: list[str] = []
    libs: list[Lib] = []
    compile_definitions: list[str] = []
    win32: bool = False
    out_dir: str = ""
    post_pyscript: str = ""
    pre_pyscript: str = ""


class ProjectConfig(pydantic.BaseModel):
    name: str = "unnamed"
    cmake_version: str = "3.30"
    language: Language = Language.CXX
    cpp_version: int = 23
    generator: Generator = Generator.Ninja
    compiler: Compiler = Compiler.Clang
    build_type: BuildType = BuildType.Debug
    architecture: Architecture = Architecture.x64
    targets: list[Target] = []
    vars: dict[str, str] = {}
    policies: dict[str, PolicyType] = {}

    def create(self, filepath: str = "CMakeLists.txt", replace: bool = True) -> None:
        """创建 CMakeLists.txt 文件
        
        Args:
            filepath: 输出文件路径
            replace: 是否替换已存在的文件
        """
        if not replace and os.path.exists(filepath):
            return
        string = ""

        string += f"cmake_minimum_required(VERSION {self.cmake_version})\n"
        string += f"\nset(project_name {self.name})\n"
        string += f"project(${{project_name}} LANGUAGES {self.language.value})\n"
        string += f"\nset(CMAKE_CXX_STANDARD {self.cpp_version})\n"
        string += "set(CMAKE_CXX_STANDARD_REQUIRED ON)\n"

        for policy, value in self.policies.items():
            string += f"cmake_policy(SET {policy} {value.value})\n"

        for var, value in self.vars.items():
            string += f"set({var} {value})\n"
        string += "\n"

        for t in self.targets:
            links = []
            include_dirs = t.include_dirs.copy()
            for lib in t.libs:
                for var, value in lib.vars.items():
                    string += f"set({var} {value})\n"
                if lib.type == LibType.HeaderOnly:
                    include_dirs += lib.include_dir
                    if lib.home:
                        string += f"set({lib.name}_DIR {lib.home})\n"
                        component = ""
                        for c in lib.components:
                            if not component:
                                component = f"COMPONENTS {c}"
                            else:
                                component += f" {c}"
                        string += f"find_package({lib.name} {component} REQUIRED)\n"
                else:
                    if lib.home:
                        match lib.search_type:
                            case LibSearchType.DIR:
                                string += f"set({lib.name}_DIR {lib.home})\n"
                            case LibSearchType.ROOT:
                                string += f"set({lib.name}_ROOT {lib.home})\n"
                            case LibSearchType.PREFIX_PATH:
                                string += f"list(APPEND {lib.name}_PREFIX_PATH {lib.home})\n"
                        component = ""
                        for c in lib.components:
                            if not component:
                                component = f"COMPONENTS {c}"
                            else:
                                component += f" {c}"
                        string += f"find_package({lib.name} {component} REQUIRED)\n"
                    else:
                        include_dirs += lib.include_dir
                string += "\n"
                links += lib.links
                if lib.components_link:
                    links += [f"{lib.name}::{i}" for i in lib.components]

            if t.type == TargetType.Executable:
                string += f"add_executable({t.name})\n"
            elif t.type == TargetType.StaticLibrary:
                string += f"add_library({t.name} STATIC)\n"
            elif t.type == TargetType.DynamicLibrary:
                string += f"add_library({t.name} SHARED)\n"
            elif t.type == TargetType.PyBind11Module:
                string += f"pybind11_add_module({t.name} MODULE)\n"
            elif t.type == TargetType.PyBind11SharedLibrary:
                string += f"pybind11_add_library({t.name} SHARED)\n"

            string += f"target_sources({t.name} PRIVATE {' '.join(t.src_files)})\n"
            if len(include_dirs) > 0:
                string += f"target_include_directories({t.name} PRIVATE {' '.join(include_dirs)})\n"
            if len(links) > 0:
                string += f"target_link_libraries({t.name} PRIVATE {' '.join(links)})\n"
            if len(t.compile_options) > 0:
                string += f"target_compile_options({t.name} PRIVATE {' '.join(t.compile_options)})\n"
            if len(t.compile_definitions) > 0:
                string += f"target_compile_definitions({t.name} PRIVATE {' '.join(t.compile_definitions)})\n"
            if t.win32:
                string += f"set_target_properties({t.name} PROPERTIES WIN32_EXECUTABLE TRUE)\n"
            if t.out_dir:
                string += f"set_target_properties({t.name} PROPERTIES RUNTIME_OUTPUT_DIRECTORY {t.out_dir})\n"

            if t.pre_pyscript:
                pyexe = sys.executable.replace("\\", "/")
                cmd = f'add_custom_command(TARGET {t.name} PRE_BUILD COMMAND {pyexe} {t.pre_pyscript} -d ${{CMAKE_RUNTIME_OUTPUT_DIRECTORY}} -g ${{CMAKE_GENERATOR}} -b ${{CMAKE_BUILD_TYPE}} COMMENT "Running pre-build python script")'
                string += cmd

            if t.post_pyscript:
                pyexe = sys.executable.replace("\\", "/")
                cmd = f'add_custom_command(TARGET {t.name} POST_BUILD COMMAND {pyexe} {t.post_pyscript} -d ${{CMAKE_RUNTIME_OUTPUT_DIRECTORY}} -g ${{CMAKE_GENERATOR}} -b ${{CMAKE_BUILD_TYPE}} COMMENT "Running post-build python script")'
                string += cmd

        with open(filepath, "w") as f:
            f.write(string)
        subprocess.run(f"gersemi -i --list-expansion favour-expansion {filepath}", shell=True)


def find_file(path: str, suff: str = ".cpp", abspath: bool = False) -> list[str]:
    """查找指定目录下匹配后缀的文件
    
    Args:
        path: 目录路径
        suff: 文件后缀，默认为 ".cpp"
        abspath: 是否返回绝对路径
        
    Returns:
        匹配的文件路径列表
    """
    if abspath:
        path = os.path.abspath(path)
    if os.path.isdir(path):
        return [os.path.join(path, i).replace("\\", "/") for i in os.listdir(path) if i.endswith(suff)]
    else:
        return []


