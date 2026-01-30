import subprocess
import os
import sys
import json
import tomllib
import tomli_w
from typing import Dict, Any
from .configure import *
from .vscode import *
from .script import create_script
from .general import read_toml
import pybind11


def configure_launch_json() -> None:
    """配置 launch.json"""
    os.makedirs(".vscode", exist_ok=True)
    launch_json_path = ".vscode/launch.json"
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "pybind11: test",
                "type": "debugpy",
                "request": "launch",
                "program": "test.py",
                "console": "integratedTerminal",
                "preLaunchTask": "CMake: build",
            }
        ],
    }

    if os.path.exists(launch_json_path):
        try:
            with open(launch_json_path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
            configs = existing_config.get("configurations", [])
            if not any(c.get("name") == "pybind11: test" for c in configs):
                configs.append(launch_config["configurations"][0])
                existing_config["configurations"] = configs
                launch_config = existing_config
        except (json.JSONDecodeError, OSError, KeyError) as e:
            print(f"Error reading launch.json: {e}")

    with open(launch_json_path, "w", encoding="utf-8") as f:
        json.dump(launch_config, f, indent=4, ensure_ascii=False)


def pybind11_init(project_name: str = "demo", script: bool = False) -> None:
    """初始化 Pybind11 项目
    
    Args:
        project_name: 项目名称
        script: 是否生成 Python 脚本配置文件
    """
    print("pybind11 initialization...")
    config_file = "cpptools.py" if script else "cpptools.toml"
    if os.path.exists(config_file):
        print(f"init failed cause {config_file} already exists")
        return

    # 通过sys获取Python路径
    py_dir = sys.prefix.replace("\\", "/")
    pybind11_dir = os.path.dirname(pybind11.__file__.replace("\\", "/"))
    pybind11_cmake_path = os.path.join(pybind11_dir, "share", "cmake", "pybind11").replace("\\", "/")

    # 获取Python版本号
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    python = Lib(
        name="Python",
        home=py_dir,
        components=["Interpreter", "Development"],
        components_link=False,
        search_type=LibSearchType.ROOT,
    )
    pybind11_lib = Lib(
        name="pybind11",
        home=pybind11_cmake_path,
        components_link=False,
        vars={"PYBIND11_PYTHON_VERSION": python_version},
    )

    # 创建目标配置
    target = Target(
        name=project_name,
        type=TargetType.PyBind11Module,
        src_files=["src/pywrapper.cpp"],
        include_dirs=["src"],
        libs=[python, pybind11_lib],
    )

    # 创建项目配置
    project = ProjectConfig(
        name=project_name,
        cmake_version="3.30",
        cpp_version=23,
        targets=[target],
    )

    # 生成配置文件
    if script:
        script_content = create_script("cpptools.py", project)
        with open("cpptools.py", "w", encoding="utf-8") as f:
            f.write(script_content)
        configure_vscode(project, script=True)
        configure_launch_json()
        print("create cpptools.py")
    else:
        with open("cpptools.toml", "wb") as f:
            print("create cpptools.toml")
            tomli_w.dump(project.model_dump(), f)

    # 创建源文件目录和文件
    if os.path.isdir("src"):
        print("skip create src because directory already exists")
    else:
        os.makedirs("src")
        with open("src/pywrapper.cpp", "w") as f:
            f.write("#include <pybind11/pybind11.h>\n")
            f.write(f"\n\nPYBIND11_MODULE({project_name}, m) {{\n")
            f.write(f'    m.doc() = "{project_name} module";\n')
            f.write("}\n")

    with open(f"test.py", "w") as f:
        f.write("import sys\n")
        f.write('sys.path.extend(["build","build/Debug","build/Release"])\n')
        f.write(f"import {project_name}\n")
        f.write(f"\nprint({project_name}.__doc__)\n")

    print("pybind11 init finished!")


def pybind11_configure() -> None:
    """配置 Pybind11 项目
    
    读取 cpptools.toml 配置文件并生成 CMakeLists.txt 和 VS Code 配置
    """
    if not (d := read_toml("./cpptools.toml")):
        print("configure failed cause cpptools.toml not found")
        return

    project = ProjectConfig(**d)

    # 生成 CMakeLists.txt
    project.create(replace=True)

    # 配置 VSCode 设置
    vst = get_vscode_settings()
    ev = vst.get("cmake.environment", {})
    evp = ev.get("PATH", "${env:PATH}")
    for t in project.targets:
        for l in t.libs:
            for b in l.bin:
                if b not in evp:
                    evp = b + ";" + evp
    if evp != "":
        ev["PATH"] = evp
        vst["cmake.environment"] = ev

    vst["cmake.generator"] = project.generator.value
    vst["cmake.debugConfig"] = {"console": "integratedTerminal"}
    vst["cmake.outputLogEncoding"] = "utf-8"
    vst["clangd.arguments"] = [
        "--compile-commands-dir=${workspaceFolder}/build",
        "--clang-tidy",
        "--header-insertion=never",
        "--pch-storage=memory",
        "--function-arg-placeholders=0",
    ]
    vst["cmake.configureSettings"] = {"CMAKE_BUILD_TYPE": "${buildType}"}
    set_vscode_settings(vst)

    # 配置 launch.json（非 script 模式）
    configure_launch_json()

    print("pybind11 configure finished!")
