from .pybind11 import pybind11_init, pybind11_configure
from .general import cmake_project_init, cmake_project_configure, create_local_pycpp_configfile
import argparse
import os
import shutil
from . import configure
from . import vscode


def remove(path: str) -> None:
    """删除文件或目录
    
    Args:
        path: 要删除的文件或目录路径
    """
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    except (OSError, PermissionError, FileNotFoundError) as e:
        print(f"Error removing {path}: {e}")


def cpp_tools() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    pybind11_parser = subparsers.add_parser("pybind11", help="pybind11 related operations")
    pybind11_parser.add_argument("--name", type=str, default="demo", help="the name of the project")
    pybind11_parser.add_argument("--script", action="store_true", help="generate cpptools.py instead of cpptools.toml")
    clean_parser = subparsers.add_parser("clean", help="clean the directory")
    init_parser = subparsers.add_parser("init", help="initialize a new cmake c++ project")
    init_parser.add_argument("--name", type=str, default="demo", help="the name of the project")
    init_parser.add_argument("--libs", type=str, nargs="*", default=[], help="the libraries of the project (multiple allowed)")
    init_parser.add_argument("--script", action="store_true", help="generate cpptools.py instead of cpptools.toml")
    configure_parser = subparsers.add_parser("configure", help="configure the project")
    create_local_pycpp_configfile_parser = subparsers.add_parser("create-local-config", help="create a local pycpp config file")
    args = parser.parse_args()
    if args.command == "pybind11":
        pybind11_init(args.name, args.script)
    elif args.command == "clean":
        for i in os.listdir("."):
            remove(i)
    elif args.command == "init":
        cmake_project_init(args.name, args.libs, args.script)
    elif args.command == "configure":
        import tomllib

        if os.path.exists("cpptools.toml"):
            with open("cpptools.toml", "rb") as f:
                config = tomllib.load(f)
            # 检查是否是 pybind11 项目
            is_pybind11 = False
            if "targets" in config:
                for target in config["targets"]:
                    if target.get("type") in ["PyBind11Module", "PyBind11SharedLibrary"]:
                        is_pybind11 = True
                        break
            if is_pybind11:
                pybind11_configure()
            else:
                cmake_project_configure()
        else:
            print("configure failed because cpptools.toml not found")
    elif args.command == "create-local-config":
        create_local_pycpp_configfile()
    else:
        parser.print_help()


__all__ = ["cpp_tools", "configure", "vscode"]
