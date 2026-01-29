"""
Language server definitions and configuration.

Provides configuration for various language servers with support for
auto-installation from GitHub releases.
"""

from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx


@dataclass
class LanguageServerConfig:
    """Configuration for a language server."""

    # Identification
    name: str
    language_ids: list[str]

    # How to run the server
    command: list[str]
    args: list[str] = field(default_factory=list)

    # Optional initialization options
    initialization_options: dict[str, Any] = field(default_factory=dict)

    # Installation
    install_command: list[str] | None = None
    github_repo: str | None = None  # e.g., "rust-lang/rust-analyzer"
    github_asset_pattern: str | None = None  # e.g., "rust-analyzer-{platform}"

    # Settings
    settings: dict[str, Any] = field(default_factory=dict)

    def get_executable(self) -> str | None:
        """Get the path to the server executable."""
        if not self.command:
            return None

        exe = self.command[0]

        # Check if it's in PATH
        which = shutil.which(exe)
        if which:
            return which

        # Check in installation directory
        install_dir = get_lsp_install_dir()
        exe_path = install_dir / exe
        if exe_path.exists():
            return str(exe_path)

        # Check with .exe on Windows
        if platform.system() == "Windows":
            exe_path = install_dir / f"{exe}.exe"
            if exe_path.exists():
                return str(exe_path)

        return None

    def is_installed(self) -> bool:
        """Check if the server is installed."""
        return self.get_executable() is not None

    async def install(self) -> bool:
        """Install the language server."""
        if self.install_command:
            return await self._install_via_command()
        elif self.github_repo:
            return await self._install_from_github()
        return False

    async def _install_via_command(self) -> bool:
        """Install via system command."""
        if not self.install_command:
            return False

        try:
            proc = subprocess.run(
                self.install_command,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return proc.returncode == 0
        except Exception:
            return False

    async def _install_from_github(self) -> bool:
        """Install from GitHub releases."""
        if not self.github_repo or not self.github_asset_pattern:
            return False

        # Determine platform
        system = platform.system().lower()
        machine = platform.machine().lower()

        if machine in ("x86_64", "amd64"):
            arch = "x86_64"
        elif machine in ("aarch64", "arm64"):
            arch = "aarch64"
        else:
            arch = machine

        platform_str = f"{system}-{arch}"

        # Get latest release
        url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                resp.raise_for_status()
                release = resp.json()

                # Find matching asset
                asset_pattern = self.github_asset_pattern.format(platform=platform_str)
                asset_url = None

                for asset in release.get("assets", []):
                    name = asset.get("name", "")
                    if asset_pattern in name:
                        asset_url = asset.get("browser_download_url")
                        break

                if not asset_url:
                    return False

                # Download and extract
                return await self._download_and_install(asset_url)

        except Exception:
            return False

    async def _download_and_install(self, url: str) -> bool:
        """Download and install from URL."""
        install_dir = get_lsp_install_dir()
        install_dir.mkdir(parents=True, exist_ok=True)

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()

                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    f.write(resp.content)
                    temp_path = Path(f.name)

                try:
                    # Extract based on file type
                    if url.endswith(".tar.gz") or url.endswith(".tgz"):
                        with tarfile.open(temp_path, "r:gz") as tar:
                            tar.extractall(install_dir)
                    elif url.endswith(".zip"):
                        with zipfile.ZipFile(temp_path, "r") as z:
                            z.extractall(install_dir)
                    else:
                        # Assume it's a binary
                        exe_name = self.command[0]
                        exe_path = install_dir / exe_name
                        shutil.copy(temp_path, exe_path)
                        os.chmod(exe_path, os.stat(exe_path).st_mode | stat.S_IEXEC)

                    return True
                finally:
                    temp_path.unlink(missing_ok=True)

        except Exception:
            return False


def get_lsp_install_dir() -> Path:
    """Get the directory for LSP server installations."""
    config_dir = Path.home() / ".config" / "pinkyclawd"
    return config_dir / "lsp-servers"


# Language server configurations
LANGUAGE_SERVERS: dict[str, LanguageServerConfig] = {
    # Python - pyright (recommended) or pylsp
    "pyright": LanguageServerConfig(
        name="pyright",
        language_ids=["python"],
        command=["pyright-langserver"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "pyright"],
    ),
    "pylsp": LanguageServerConfig(
        name="pylsp",
        language_ids=["python"],
        command=["pylsp"],
        install_command=["pip", "install", "python-lsp-server"],
    ),
    # TypeScript/JavaScript
    "typescript-language-server": LanguageServerConfig(
        name="typescript-language-server",
        language_ids=["typescript", "typescriptreact", "javascript", "javascriptreact"],
        command=["typescript-language-server"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "typescript-language-server", "typescript"],
    ),
    # Rust
    "rust-analyzer": LanguageServerConfig(
        name="rust-analyzer",
        language_ids=["rust"],
        command=["rust-analyzer"],
        github_repo="rust-lang/rust-analyzer",
        github_asset_pattern="rust-analyzer-{platform}",
    ),
    # Go
    "gopls": LanguageServerConfig(
        name="gopls",
        language_ids=["go", "go.mod"],
        command=["gopls"],
        install_command=["go", "install", "golang.org/x/tools/gopls@latest"],
    ),
    # C/C++
    "clangd": LanguageServerConfig(
        name="clangd",
        language_ids=["c", "cpp"],
        command=["clangd"],
        args=["--background-index"],
    ),
    # Java
    "jdtls": LanguageServerConfig(
        name="jdtls",
        language_ids=["java"],
        command=["jdtls"],
    ),
    # Kotlin
    "kotlin-language-server": LanguageServerConfig(
        name="kotlin-language-server",
        language_ids=["kotlin"],
        command=["kotlin-language-server"],
        github_repo="fwcd/kotlin-language-server",
        github_asset_pattern="server",
    ),
    # Ruby
    "solargraph": LanguageServerConfig(
        name="solargraph",
        language_ids=["ruby"],
        command=["solargraph"],
        args=["stdio"],
        install_command=["gem", "install", "solargraph"],
    ),
    # PHP
    "intelephense": LanguageServerConfig(
        name="intelephense",
        language_ids=["php"],
        command=["intelephense"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "intelephense"],
    ),
    # HTML/CSS
    "vscode-html-language-server": LanguageServerConfig(
        name="vscode-html-language-server",
        language_ids=["html"],
        command=["vscode-html-language-server"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "vscode-langservers-extracted"],
    ),
    "vscode-css-language-server": LanguageServerConfig(
        name="vscode-css-language-server",
        language_ids=["css", "scss", "less"],
        command=["vscode-css-language-server"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "vscode-langservers-extracted"],
    ),
    # JSON
    "vscode-json-language-server": LanguageServerConfig(
        name="vscode-json-language-server",
        language_ids=["json", "jsonc"],
        command=["vscode-json-language-server"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "vscode-langservers-extracted"],
    ),
    # YAML
    "yaml-language-server": LanguageServerConfig(
        name="yaml-language-server",
        language_ids=["yaml"],
        command=["yaml-language-server"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "yaml-language-server"],
    ),
    # Bash
    "bash-language-server": LanguageServerConfig(
        name="bash-language-server",
        language_ids=["shellscript"],
        command=["bash-language-server"],
        args=["start"],
        install_command=["npm", "install", "-g", "bash-language-server"],
    ),
    # Dockerfile
    "dockerfile-language-server": LanguageServerConfig(
        name="dockerfile-language-server",
        language_ids=["dockerfile"],
        command=["docker-langserver"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "dockerfile-language-server-nodejs"],
    ),
    # Lua
    "lua-language-server": LanguageServerConfig(
        name="lua-language-server",
        language_ids=["lua"],
        command=["lua-language-server"],
        github_repo="LuaLS/lua-language-server",
        github_asset_pattern="lua-language-server-{platform}",
    ),
    # Elixir
    "elixir-ls": LanguageServerConfig(
        name="elixir-ls",
        language_ids=["elixir"],
        command=["elixir-ls"],
        github_repo="elixir-lsp/elixir-ls",
        github_asset_pattern="elixir-ls",
    ),
    # Haskell
    "haskell-language-server": LanguageServerConfig(
        name="haskell-language-server",
        language_ids=["haskell"],
        command=["haskell-language-server-wrapper"],
        args=["--lsp"],
        github_repo="haskell/haskell-language-server",
        github_asset_pattern="haskell-language-server-{platform}",
    ),
    # Zig
    "zls": LanguageServerConfig(
        name="zls",
        language_ids=["zig"],
        command=["zls"],
        github_repo="zigtools/zls",
        github_asset_pattern="zls-{platform}",
    ),
    # Svelte
    "svelte-language-server": LanguageServerConfig(
        name="svelte-language-server",
        language_ids=["svelte"],
        command=["svelteserver"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "svelte-language-server"],
    ),
    # Vue
    "volar": LanguageServerConfig(
        name="volar",
        language_ids=["vue"],
        command=["vue-language-server"],
        args=["--stdio"],
        install_command=["npm", "install", "-g", "@vue/language-server"],
    ),
    # Terraform
    "terraform-ls": LanguageServerConfig(
        name="terraform-ls",
        language_ids=["terraform"],
        command=["terraform-ls"],
        args=["serve"],
        github_repo="hashicorp/terraform-ls",
        github_asset_pattern="terraform-ls_{platform}",
    ),
    # GraphQL
    "graphql-language-server": LanguageServerConfig(
        name="graphql-language-server",
        language_ids=["graphql"],
        command=["graphql-lsp"],
        args=["server", "-m", "stream"],
        install_command=["npm", "install", "-g", "graphql-language-service-cli"],
    ),
    # Markdown
    "marksman": LanguageServerConfig(
        name="marksman",
        language_ids=["markdown"],
        command=["marksman"],
        args=["server"],
        github_repo="artempyanykh/marksman",
        github_asset_pattern="marksman-{platform}",
    ),
    # TOML
    "taplo": LanguageServerConfig(
        name="taplo",
        language_ids=["toml"],
        command=["taplo"],
        args=["lsp", "stdio"],
        github_repo="tamasfe/taplo",
        github_asset_pattern="taplo-{platform}",
    ),
}


def get_server_for_language(language_id: str) -> LanguageServerConfig | None:
    """
    Get the recommended language server for a language.

    Args:
        language_id: LSP language ID

    Returns:
        Server configuration or None if no server available
    """
    # Priority order for servers
    priority = [
        # Python - prefer pyright
        "pyright",
        "pylsp",
        # TypeScript/JavaScript
        "typescript-language-server",
        # Rust
        "rust-analyzer",
        # Go
        "gopls",
        # C/C++
        "clangd",
        # Others follow
    ]

    # First check priority servers
    for name in priority:
        server = LANGUAGE_SERVERS.get(name)
        if server and language_id in server.language_ids:
            return server

    # Then check all servers
    for server in LANGUAGE_SERVERS.values():
        if language_id in server.language_ids:
            return server

    return None


def list_available_servers() -> list[str]:
    """List all available language servers."""
    return list(LANGUAGE_SERVERS.keys())


def get_installed_servers() -> list[LanguageServerConfig]:
    """Get all installed language servers."""
    return [s for s in LANGUAGE_SERVERS.values() if s.is_installed()]
