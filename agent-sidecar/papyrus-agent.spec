# PyInstaller spec for the Papyrus agent sidecar (single-file executable).
# Build with: uv run python scripts/build_sidecar.py
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = []
for package in (
    "uvicorn",
    "papyrus_agent",
    "langchain_openai",
    "langchain_ollama",
    "langgraph",
):
    hiddenimports += collect_submodules(package)

datas = []
for package in ("langchain_core", "langgraph"):
    datas += collect_data_files(package)

a = Analysis(
    ["run_sidecar.py"],
    pathex=["src"],
    datas=datas,
    hiddenimports=hiddenimports,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="papyrus-agent",
    console=True,
    upx=False,
)
