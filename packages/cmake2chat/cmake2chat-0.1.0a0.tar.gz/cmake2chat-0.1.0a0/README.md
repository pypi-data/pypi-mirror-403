# `cmake2chat`

Lost in a huge CMake project? Wish an LLM could just "see" the codebase structure and all build rules? Now they can!

## What's This?

`cmake2chat` scans your CMake project directory, builds a tree view of the codebase, and exports the tree view, the paths of all `CMakeLists.txt` files along with their contents to an OpenAI Chat Completions-compatible JSON.

### Typical Use Cases

- Instant overview: Give an LLM a complete picture of your project's structure (files, folders) plus CMake build logic at every level.
- Build-system-powered Q&A: Ask questions like "What libraries does this project build?", "Where is the executable defined?", or "What targets/flags are set in this module?" and get relevant, context-based answers!
- AI onboarding: Drop into a new CMake project and let an LLM guide you using actual high-level structure and build scripts, not just guesses.
- No manual plumbing: Skip hours of clicking/repeating `find .`, opening dozens of files, or pasting snippets piecemeal. Feed the AI the *whole map* and let it answer or advise precisely.

## Install

```bash
pip install cmake2chat
```

## Example

Suppose you have the following CMake project directory structure:

```
- my_project/
  - CMakeLists.txt
  - src/
    - CMakeLists.txt
    - main.cpp
  - lib/
    - CMakeLists.txt
```

To generate an OpenAI Chat Completions-compatible JSON describing your project, simply run:

```bash
python -m cmake2chat my_project -o my_project.json
```

An example of the beginning of the output might look like:

```json
[
  {
    "role": "user",
    "content": "- my_project/\n  - CMakeLists.txt\n  - src/\n    - CMakeLists.txt\n    - main.cpp\n  - lib/\n    - CMakeLists.txt"
  },
  {
    "role": "user",
    "content": "CMakeLists.txt"
  },
  {
    "role": "user",
    "content": "# Top-level build logic goes here\ncmake_minimum_required(VERSION 3.10)\nproject(MyProject)\n..."
  },
  {
    "role": "user",
    "content": "src/CMakeLists.txt"
  },
  {
    "role": "user",
    "content": "# Build logic for src directory\nadd_executable(main main.cpp)\n..."
  }
]
```

You can now use this JSON directly as input to an LLM API for a powerful, context-aware understanding of your CMake project!

## How it works

- **Scan**: Recursively walks your project directory.
- **Map**: Extracts the structure (files & folders) as a tree.
- **Collect**: For each `CMakeLists.txt`, grabs its path and full content.
- **Export**: Outputs everything as an OpenAI Chat Completions-compatible JSON.

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
