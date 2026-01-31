# Dumpster

Dumpster is a tool to create a single-file context dump of your codebase, perfect for AI analysis and documentation.

## Features

- Collects code from multiple files into one output file
- Supports Git integration for version information
- Configurable through dump.yaml
- Handles various textual files

## Installation

```bash
pip install dumpster-cli
```

## Usage

1. Create a dump.yaml configuration file:
```yaml
output: sources.txt
extensions:
  - .py
  - .md
  - .yaml
contents:
  - "**/*.py"
  - "**/*.md"
```

You can also use `dumpster-cli init` to create a stub `dump.yaml` and create/update the local `.gitignore`

2. Run the dump command:

```bash
dumpster-cli
```

optionally you can create a subset of the dump with

```bash
dumpster-cli --contents ./folder1 --contents ./other/folder/myfile.py
```


## Configuration

The `dump.yaml` file supports these options:

- `output`: Output file path (default: sources.txt)
- `extensions`: List of file extensions to include
- `contents`: Patterns of files to include
- `exclude`: Patterns of files to exclude
- `prompt`: Optional prompt text
- `header`: Optional header text
- `footer`: Optional footer text

## Git Integration

Dumpster automatically includes Git metadata in the output:
- Repository root
- Current branch
- Commit hash
- Commit time
- Author information
- Dirty status

## Development

Dumpster uses these dependencies:
- GitPython for Git operations
- Pydantic for configuration validation
- PyYAML for YAML parsing

The project follows semantic versioning and uses uv for dependency management.

## LICENSE

Copyright >=2025 muka

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
