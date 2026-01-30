import os
import shutil
import sys
import tomllib
import tomli_w
from typing import Dict, Any
from .configure import *
from .vscode import *
from .script import create_script


def read_toml(path: str) -> Dict[str, Any]:
    """读取 TOML 配置文件
    
    Args:
        path: TOML 文件路径
        
    Returns:
        解析后的字典，如果文件不存在则返回空字典
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        print(f"Error reading TOML file {path}: {e}")
        return {}


def create_local_pycpp_configfile() -> None:
    """创建本地 pycpp 配置文件"""
    path = os.path.expanduser("~/.cpptools/default_init.toml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    shutil.copy(os.path.join(os.path.dirname(__file__), "default.toml"), path)
    print("local pycpp config file created! file location: ", path)


def cmake_project_init(project_name: str = "", libs: list[str] = None, script: bool = False) -> None:
    """初始化 CMake C++ 项目
    
    Args:
        project_name: 项目名称
        libs: 要包含的库列表
        script: 是否生成 Python 脚本配置文件
    """
    if libs is None:
        libs = []
    path = os.path.expanduser("~/.cpptools/default_init.toml")
    custom_config = read_toml(path)
    path = os.path.join(os.path.dirname(__file__), "default.toml")
    default_config = read_toml(path)
    cfg = custom_config if custom_config != {} else default_config
    
    config_file = "cpptools.py" if script else "cpptools.toml"
    if os.path.exists(config_file):
        print(f"init failed cause {config_file} already exists")
        return

    if os.path.isdir("src"):
        print("skip create src because directory already exists")
    else:
        os.makedirs("src")
        with open("src/main.cpp", "w", encoding="utf-8") as f:
            f.write("#include <iostream>\n")
            f.write(f"\nint main(int argc,char *argv[]) {{\n")
            f.write(f'    std::cout << "Hello, World!" << std::endl;\n')
            f.write("    return 0;\n")
            f.write("}\n")

    libraries: list[Lib] = []
    for i in libs:
        if i in cfg["libs"]:
            lib = cfg["libs"][i]
            lib = Lib(**lib)
            libraries.append(lib)

    target = Target(
        name=project_name,
        type=TargetType.Executable,
        src_files=["src/main.cpp"],
        include_dirs=["src"],
    )
    target.libs += libraries
    project = ProjectConfig(name=project_name, targets=[target])

    if script:
        script_content = create_script("cpptools.py", project)
        with open("cpptools.py", "w", encoding="utf-8") as f:
            f.write(script_content)
        configure_vscode(project,script=True)
        print("create cpptools.py")
    else:
        with open("cpptools.toml", "wb") as f:
            print("create cpptools.toml")
            tomli_w.dump(project.model_dump(), f)
        configure_vscode(project,script=False)


def cmake_project_configure(script: bool = False) -> None:
    """配置 CMake 项目
    
    Args:
        script: 是否使用 Python 脚本配置
    """
    if d := read_toml("./cpptools.toml"):
        project = ProjectConfig(**d)
        project.create(replace=True)
        configure_vscode(project, script)
