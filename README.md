# Tauri + React + Typescript

This template should help get you started developing with Tauri, React and Typescript in Vite.

## Building the Python sidecar

The agent in `agent-sidecar/` is bundled with PyInstaller and launched by Tauri as an external binary. Build it before running `tauri dev` or `tauri build`, and again after any Python change:

```sh
npm run sidecar:build
```

This needs [uv](https://docs.astral.sh/uv/) and Rust (`rustc`) installed. It runs `agent-sidecar/scripts/build_sidecar.py`, which writes the executable to `src-tauri/binaries/papyrus-agent-<target-triple>`. That folder is gitignored.

Notes:

- Tauri fails to build if the binary is missing.
- PyInstaller can't cross-compile, so build on each target OS and architecture.
- The sidecar reads `PAPYRUS_*` settings from the environment (see `agent-sidecar/.envrc`).

## Recommended IDE Setup

- [VS Code](https://code.visualstudio.com/) + [Tauri](https://marketplace.visualstudio.com/items?itemName=tauri-apps.tauri-vscode) + [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)
