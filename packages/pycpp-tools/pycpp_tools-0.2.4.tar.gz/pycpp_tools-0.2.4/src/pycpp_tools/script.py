from .configure import *


def create_script(path: str, p: ProjectConfig) -> str:
    """创建 Python 脚本配置文件
    
    Args:
        path: 脚本文件路径
        p: 项目配置对象
        
    Returns:
        生成的脚本内容字符串
    """
    tab = " " * 4
    tab2 = tab * 2
    tab3 = tab * 3
    
    # 生成 ProjectConfig 的属性
    config_lines = []
    config_lines.append(f"name=\"{p.name}\"")
    if p.cmake_version != "3.30":
        config_lines.append(f"cmake_version=\"{p.cmake_version}\"")
    if p.language != Language.CXX:
        config_lines.append(f"language=Language.{p.language.value}")
    if p.cpp_version != 23:
        config_lines.append(f"cpp_version={p.cpp_version}")
    if p.generator != Generator.Ninja:
        config_lines.append(f"generator=Generator.{p.generator.value}")
    if p.compiler != Compiler.Clang:
        config_lines.append(f"compiler=Compiler.{p.compiler.value}")
    if p.build_type != BuildType.Debug:
        config_lines.append(f"build_type=BuildType.{p.build_type.value}")
    if p.architecture != Architecture.x64:
        config_lines.append(f"architecture=Architecture.{p.architecture.value}")
    if p.vars:
        vars_str = "{"
        vars_items = [f'"{k}": "{v}"' for k, v in p.vars.items()]
        vars_str += ", ".join(vars_items)
        vars_str += "}"
        config_lines.append(f"vars={vars_str}")
    if p.policies:
        policies_str = "{"
        policies_items = [f'"{k}": PolicyType.{v.value}' for k, v in p.policies.items()]
        policies_str += ", ".join(policies_items)
        policies_str += "}"
        config_lines.append(f"policies={policies_str}")
    
    if config_lines:
        config_str = "\n" + tab + (",\n" + tab).join(config_lines)
    else:
        config_str = ""
    
    # 生成所有 targets
    targets_code = []
    for t in p.targets:
        target_lines = []
        target_lines.append(f"name=\"{t.name}\"")
        target_lines.append(f"type=TargetType.{t.type.value}")
        
        if t.src_files:
            src_files_str = "find_file('src')"
            target_lines.append(f"src_files={src_files_str}")
        else:
            target_lines.append("src_files=find_file(\"src\")")
        
        if t.include_dirs:
            include_dirs_str = "[" + ", ".join([f'"{d}"' for d in t.include_dirs]) + "]"
            target_lines.append(f"include_dirs={include_dirs_str}")
        
        if t.compile_options:
            compile_options_str = "[" + ", ".join([f'"{o}"' for o in t.compile_options]) + "]"
            target_lines.append(f"compile_options={compile_options_str}")
        
        # 生成 libs
        if t.libs:
            libs_code = []
            for lib in t.libs:
                lib_lines = []
                lib_lines.append(f"name=\"{lib.name}\"")
                if lib.version:
                    lib_lines.append(f"version=\"{lib.version}\"")
                if lib.home:
                    lib_lines.append(f"home=\"{lib.home}\"")
                if lib.type != LibType.Dynamic:
                    lib_lines.append(f"type=LibType.{lib.type.value}")
                if lib.search_type != LibSearchType.DIR:
                    lib_lines.append(f"search_type=LibSearchType.{lib.search_type.value}")
                if lib.components:
                    components_str = "[" + ", ".join([f'"{c}"' for c in lib.components]) + "]"
                    lib_lines.append(f"components={components_str}")
                if not lib.components_link:
                    lib_lines.append(f"components_link={lib.components_link}")
                if lib.links:
                    links_str = "[" + ", ".join([f'"{l}"' for l in lib.links]) + "]"
                    lib_lines.append(f"links={links_str}")
                if lib.bin:
                    bin_str = "[" + ", ".join([f'"{b}"' for b in lib.bin]) + "]"
                    lib_lines.append(f"bin={bin_str}")
                if lib.include:
                    include_str = "[" + ", ".join([f'"{i}"' for i in lib.include]) + "]"
                    lib_lines.append(f"include={include_str}")
                if lib.vars:
                    vars_str = "{"
                    vars_items = [f'"{k}": "{v}"' for k, v in lib.vars.items()]
                    vars_str += ", ".join(vars_items)
                    vars_str += "}"
                    lib_lines.append(f"vars={vars_str}")
                
                lib_code = tab3 + "Lib(\n" + tab3 + tab + (",\n" + tab3 + tab).join(lib_lines) + "\n" + tab3 + ")"
                libs_code.append(lib_code)
            
            if libs_code:
                libs_str = "[\n" + ",\n".join(libs_code) + "\n" + tab2 + "]"
                target_lines.append(f"libs={libs_str}")
        
        if t.compile_definitions:
            compile_definitions_str = "[" + ", ".join([f'"{d}"' for d in t.compile_definitions]) + "]"
            target_lines.append(f"compile_definitions={compile_definitions_str}")
        
        if t.win32:
            target_lines.append(f"win32={t.win32}")
        
        if t.out_dir:
            target_lines.append(f"out_dir=\"{t.out_dir}\"")
        
        if t.post_pyscript:
            target_lines.append(f"post_pyscript=\"{t.post_pyscript}\"")
        
        if t.pre_pyscript:
            target_lines.append(f"pre_pyscript=\"{t.pre_pyscript}\"")
        
        target_code = tab2 + "Target(\n" + tab3 + (",\n" + tab3).join(target_lines) + "\n" + tab2 + ")"
        targets_code.append(target_code)
    
    targets_str = "[\n" + ",\n".join(targets_code) + "\n" + tab + "]" if targets_code else "[]"
    
    script = f"""from pycpp_tools.configure import *
from pycpp_tools.vscode import configure_vscode
import os

if __name__ == "__main__":
    p = ProjectConfig({config_str})
    p.targets = {targets_str}
    p.create(replace=True)
    configure_vscode(p)
    print("pycpp configure success")
"""
    return script
