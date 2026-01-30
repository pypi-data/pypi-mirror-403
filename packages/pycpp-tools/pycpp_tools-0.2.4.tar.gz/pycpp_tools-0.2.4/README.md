# pycpp-tools

A command-line utility tool to assist with CMake C++ project configuration and Pybind11 project setup.

## Features

- **CMake Project Initialization**: Quickly initialize a new CMake C++ project with customizable settings
- **Pybind11 Project Setup**: Initialize Pybind11 projects for Python-C++ bindings
- **Project Configuration**: Generate `CMakeLists.txt` from TOML configuration files or Python scripts
- **Library Management**: Easy configuration for common C++ libraries (Boost, Qt, OpenCV, Python, Pybind11, etc.)
- **VS Code Integration**: Automatically generates VS Code launch configurations and settings

## Installation

Install the package using pip:

```bash
pip install .
```

Or install in development mode:

```bash
pip install -e .
```

After installation, the `pycpp` command will be available in your terminal.

## Usage

### Important Notes on CMakeLists.txt Generation

**This tool manages `CMakeLists.txt` generation automatically.** You should use the `pycpp` command or Python scripts to generate `CMakeLists.txt` files. If you need to modify the CMake configuration, **edit the `cpptools.toml` configuration file or your `cpptools.py` script** instead of directly editing `CMakeLists.txt`, because running `pycpp configure` will overwrite the `CMakeLists.txt` file.

**Workflow:**
1. Edit `cpptools.toml` or modify your `cpptools.py` script
2. Run `pycpp configure` to regenerate `CMakeLists.txt`
3. Build your project using CMake Tools or command-line CMake

### Command-Line Interface

#### Initialize a CMake C++ Project

To initialize a new CMake C++ project:

```bash
pycpp init --name myproject
```

You can also specify libraries to include:

```bash
pycpp init --name myproject --libs boost qt opencv
```

**Options:**
- `--name <name>`: The name of the project (default: "demo")
- `--libs <libs...>`: One or more libraries to include in the project (optional)
- `--script`: Generate `cpptools.py` instead of `cpptools.toml` (allows programmatic configuration)

This command will:
- Create a `src/` directory with a basic `main.cpp` file
- Generate a `cpptools.toml` configuration file (or `cpptools.py` if `--script` is used)
- Set up the project structure

#### Configure a Project

After initializing a project, generate the `CMakeLists.txt` file:

```bash
pycpp configure
```

This command reads the `cpptools.toml` file or executes `cpptools.py` and generates:
- `CMakeLists.txt` with proper CMake configuration
- `.vscode/launch.json` for debugging
- `.vscode/settings.json` for VS Code environment settings

The command automatically detects if the project is a Pybind11 project and applies the appropriate configuration.

#### Initialize a Pybind11 Project

To set up a Pybind11 project for Python-C++ bindings:

```bash
pycpp pybind11 --name mymodule
```

**Options:**
- `--name <name>`: The name of the Pybind11 module (default: "demo")
- `--script`: Generate `cpptools.py` instead of `cpptools.toml` (allows programmatic configuration)

This will create:
- `cpptools.toml` configuration file (or `cpptools.py` if `--script` is used)
- `src/pywrapper.cpp` with a basic Pybind11 module template
- `test.py` for testing the Python module

After running `pycpp configure`, it will also generate:
- `CMakeLists.txt` configured for Pybind11
- `.vscode/launch.json` for debugging

#### Using Python Script Configuration (`--script`)

When you use the `--script` option with `pycpp init` or `pycpp pybind11`, the tool generates a `cpptools.py` file instead of `cpptools.toml`. This Python script uses the `pycpp_tools.configure` module and provides more flexibility for programmatic configuration.

**Example workflow with `--script`:**

```bash
# Initialize with script mode
pycpp init --name myproject --script

# Edit cpptools.py to customize configuration
# Then configure
pycpp configure
```

The generated `cpptools.py` file imports from `pycpp_tools.configure` and allows you to programmatically modify the project configuration before running `pycpp configure`.

#### Create Local Configuration File

To create a local default configuration file:

```bash
pycpp create-local-config
```

This creates a default configuration file at `~/.cpptools/default_init.toml` that will be used as the template for all new projects initialized with `pycpp init`.

#### Clean Directory

To clean the current directory (removes all files and directories):

```bash
pycpp clean
```

**Warning**: This command will delete all files in the current directory. Use with caution!

## Configuration

### cpptools.toml

The `cpptools.toml` file is used to configure your CMake project. Example:

```toml
project_name = "myproject"
cmake_version = "3.30"
cpp_version = 23
generator = "Ninja"

[libs]

[libs.boost]
name = "boost"
header_only = true
home = "E:/work_data/third_libs/boost_1_86_0"

[libs.qt]
name = "Qt6"
header_only = false
home = "E:/work_data/third_libs/Qt/6.10.0/msvc2022_64"
bin = "E:/work_data/third_libs/Qt/6.10.0/msvc2022_64/bin"
components = ["Widgets", "Core", "Gui"]
links = ["Qt6::Widgets", "Qt6::Core", "Qt6::Gui"]
```

### cpptools.py

When using `--script`, a Python script is generated that uses the `pycpp_tools.configure` module. You can import and modify the configuration programmatically:

```python
from pycpp_tools.configure import *
from pycpp_tools.vscode import configure_vscode
import os

if __name__ == "__main__":
    p = ProjectConfig(name="myproject")
    p.targets = [
        Target(
            name="myapp",
            type=TargetType.Executable,
            src_files=find_file("src"),
            libs=[...]
        )
    ]
    p.create(replace=True)
    configure_vscode(p)
    print("pycpp configure success")
```

### Default Configuration

You can create a default configuration file at `~/.cpptools/default_init.toml` to set default values for all new projects. The tool will merge your custom defaults with the built-in defaults.

## Python API

The `pycpp_tools.configure` module provides Python classes for programmatically configuring CMake projects. Key classes include:

- `ProjectConfig`: Main configuration class for CMake projects
- `Target`: Represents a build target (executable, library, or Pybind11 module)
- `Lib`: Represents a library dependency

For detailed API documentation, see the source code in `src/pycpp_tools/configure.py`.

## Supported Libraries

The tool supports configuration for various C++ libraries:

- **Boost**: Header-only library support
- **Qt/Qt6/Qt5**: Automatic MOC/UIC/RCC configuration
- **OpenCV**: Special handling for OpenCV runtime and architecture
- **Python3**: Python development libraries
- **Pybind11**: Python-C++ binding library

## Examples

### Example 1: Simple C++ Project

```bash
# Initialize a project
pycpp init --name hello

# Configure and generate CMakeLists.txt
pycpp configure

# Build with CMake
mkdir build
cd build
cmake ..
cmake --build .
```

### Example 2: C++ Project with Libraries

```bash
# Initialize with libraries
pycpp init --name myapp --libs boost qt

# Edit cpptools.toml to configure library paths
# Then configure
pycpp configure

# Build
mkdir build
cd build
cmake ..
cmake --build .
```

### Example 3: Pybind11 Project

```bash
# Initialize Pybind11 project
pycpp pybind11 --name mymodule

# Configure
pycpp configure

# Build
mkdir build
cd build
cmake ..
cmake --build .

# Test the Python module
python ../test.py
```

### Example 4: Using Python Script Configuration

```bash
# Initialize with script mode
pycpp init --name myproject --script

# Edit cpptools.py to customize configuration programmatically
# Then configure
pycpp configure

# Build
mkdir build
cd build
cmake ..
cmake --build .
```

## Project Structure

After initialization, a typical project structure looks like:

```
myproject/
├── src/
│   └── main.cpp
├── cpptools.toml (or cpptools.py if --script was used)
├── CMakeLists.txt (generated by configure)
└── .vscode/
    ├── launch.json (generated by configure)
    └── settings.json (generated by configure)
```

## Requirements

- Python 3.8 or higher
- CMake 3.30 or higher (configurable)
- C++ compiler supporting C++23 (configurable)

## License

MIT License

## Author

R.E. (redelephant@foxmail.com)
