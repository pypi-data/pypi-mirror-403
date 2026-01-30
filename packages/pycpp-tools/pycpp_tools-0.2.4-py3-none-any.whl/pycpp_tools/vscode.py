import pyjson5
import json
import os
from typing import Dict, Any
from .configure import ProjectConfig


def get_vscode_settings() -> Dict[str, Any]:
    """获取 VS Code 设置
    
    Returns:
        VS Code 设置字典
    """
    filepath = ".vscode/settings.json"
    if os.path.isfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                settings = pyjson5.load(f)
            return settings
        except (json.JSONDecodeError, OSError, pyjson5.Json5DecoderException) as e:
            print(f"Error reading VS Code settings: {e}")
            return {}
    else:
        return {}


def set_vscode_settings(settings: Dict[str, Any]) -> None:
    """设置 VS Code 设置
    
    Args:
        settings: VS Code 设置字典
    """
    filepath = ".vscode/settings.json"
    if not os.path.exists(".vscode"):
        os.mkdir(".vscode")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except (OSError, TypeError) as e:
        print(f"Error writing VS Code settings: {e}")


def get_vscode_tasks() -> Dict[str, Any]:
    """获取 VS Code 任务配置
    
    Returns:
        VS Code 任务配置字典
    """
    filepath = ".vscode/tasks.json"
    if os.path.isfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                settings = pyjson5.load(f)
            return settings
        except (json.JSONDecodeError, OSError, pyjson5.Json5DecoderException) as e:
            print(f"Error reading VS Code tasks: {e}")
            return {}
    else:
        return {}


def set_vscode_tasks(tasks: Dict[str, Any]) -> None:
    """设置 VS Code 任务配置
    
    Args:
        tasks: VS Code 任务配置字典
    """
    filepath = ".vscode/tasks.json"
    if not os.path.exists(".vscode"):
        os.mkdir(".vscode")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=4, ensure_ascii=False)
    except (OSError, TypeError) as e:
        print(f"Error writing VS Code tasks: {e}")


def configure_vscode(project: ProjectConfig, script: bool = True) -> None:
    # vscode tasks
    tsk = get_vscode_tasks()
    tsk["version"] = "2.0.0"
    t1 = {
        "label": "pycpp create configure",
        "type": "shell",
        "command": "python cpptools.py" if script else "pycpp configure",
        "options": {"cwd": "${workspaceFolder}"},
        "problemMatcher": [],
    }
    t2 = {
        "label": "pycpp configure",
        "dependsOn": ["pycpp create configure", "CMake: configure"],
        "dependsOrder": "sequence",
        "problemMatcher": [],
    }

    for t in [t1, t2]:
        if t not in tsk.get("tasks", []):
            tsk["tasks"] = tsk.get("tasks", []) + [t]
    set_vscode_tasks(tsk)
    # vscode settings
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
    t = {
        "label": "$(server-environment) configure",
        "task": "pycpp configure",
        "tooltip": "pycpp && configure",
    }
    if t not in vst.get("VsCodeTaskButtons.tasks", []):
        vst["VsCodeTaskButtons.tasks"] = vst.get("VsCodeTaskButtons.tasks", []) + [t]
    set_vscode_settings(vst)
