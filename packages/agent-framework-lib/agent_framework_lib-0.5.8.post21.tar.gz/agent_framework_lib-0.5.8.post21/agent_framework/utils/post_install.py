"""
Post-installation script for agent-framework-lib.

This script automatically installs:
- Playwright browsers (for chart/mermaid/table image generation)
- Deno runtime (for MCP servers like mcp-run-python)

It provides lazy initialization for tools that need these dependencies.
"""

import subprocess
import sys
import logging
import os
import platform
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# Track if we've already attempted installation in this process
_playwright_install_attempted = False
_playwright_browsers_available = None
_deno_install_attempted = False
_deno_available = None
_deno_path = None


def _check_playwright_browsers_installed() -> bool:
    """
    Check if Playwright Chromium browser is already installed.
    
    Uses playwright's internal API to check browser installation status.
    """
    try:
        # Try to import playwright and check if chromium is installed
        from playwright._impl._driver import compute_driver_executable
        
        # Get the browsers path
        driver_executable = compute_driver_executable()
        browsers_path = Path(driver_executable).parent.parent / "chromium"
        
        # Check if chromium directory exists and has content
        if browsers_path.exists() and any(browsers_path.iterdir()):
            return True
        return False
    except Exception:
        # Fallback: try to launch chromium and see if it works
        try:
            result = subprocess.run(
                [sys.executable, "-c", 
                 "from playwright.sync_api import sync_playwright; "
                 "p = sync_playwright().start(); "
                 "b = p.chromium.launch(headless=True); "
                 "b.close(); p.stop(); print('OK')"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0 and "OK" in result.stdout
        except Exception:
            return False


def _check_playwright_can_launch() -> tuple[bool, str | None]:
    """
    Check if Playwright can actually launch a browser (tests system dependencies).
    
    Returns:
        Tuple of (can_launch: bool, error_message: str | None)
    """
    try:
        result = subprocess.run(
            [sys.executable, "-c", 
             "from playwright.sync_api import sync_playwright; "
             "p = sync_playwright().start(); "
             "b = p.chromium.launch(headless=True); "
             "b.close(); p.stop(); print('OK')"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and "OK" in result.stdout:
            return True, None
        
        # Check for system dependency errors
        error_output = result.stderr or result.stdout or ""
        if "missing dependencies" in error_output.lower() or "install-deps" in error_output:
            return False, "system_deps"
        return False, error_output[:500]
    except Exception as e:
        return False, str(e)


def _is_root() -> bool:
    """Check if running as root user."""
    try:
        return os.geteuid() == 0
    except AttributeError:
        # Windows doesn't have geteuid
        return False


def _sudo_prefix() -> list[str]:
    """Return sudo prefix if not running as root."""
    return [] if _is_root() else ["sudo"]


def _install_playwright_system_deps() -> tuple[bool, str | None]:
    """
    Attempt to install Playwright system dependencies on Linux.
    
    Tries multiple methods:
    1. playwright install-deps (with sudo if needed)
    2. apt-get install with the required libraries
    
    Returns:
        Tuple of (success: bool, message: str | None)
    """
    system = platform.system().lower()
    
    if system != "linux":
        return True, None  # Not needed on non-Linux
    
    logger.info("🔧 Installing Playwright system dependencies...")
    sudo = _sudo_prefix()
    
    # Method 1: Try playwright install-deps (preferred)
    logger.info("   Trying: playwright install-deps chromium...")
    try:
        result = subprocess.run(
            sudo + [sys.executable, "-m", "playwright", "install-deps", "chromium"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            logger.info("✅ Playwright system dependencies installed successfully")
            return True, None
    except Exception as e:
        logger.debug(f"   playwright install-deps failed: {e}")
    
    # Method 2: Try apt-get directly
    logger.info("   Trying: apt-get install...")
    try:
        # First run apt-get update
        logger.info("   Running: apt-get update...")
        update_result = subprocess.run(
            sudo + ["apt-get", "update"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if update_result.returncode == 0:
            # Try with libasound2t64 first (newer Ubuntu/Debian)
            logger.info("   Running: apt-get install -y libnspr4 libnss3 libasound2t64...")
            install_result = subprocess.run(
                sudo + ["apt-get", "install", "-y", "libnspr4", "libnss3", "libasound2t64"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if install_result.returncode == 0:
                logger.info("✅ Playwright system dependencies installed successfully")
                return True, None
            
            # Fallback: try with libasound2 (older systems)
            logger.info("   Retrying with libasound2 (older package name)...")
            install_result = subprocess.run(
                sudo + ["apt-get", "install", "-y", "libnspr4", "libnss3", "libasound2"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if install_result.returncode == 0:
                logger.info("✅ Playwright system dependencies installed successfully")
                return True, None
    except subprocess.TimeoutExpired:
        logger.warning("   apt-get timed out")
    except FileNotFoundError:
        logger.warning("   apt-get not found (not a Debian/Ubuntu system?)")
    except Exception as e:
        logger.warning(f"   apt-get failed: {e}")
    
    # All methods failed, provide manual instructions
    instructions = (
        "⚠️  Could not automatically install Playwright system dependencies.\n"
        "   Please run one of the following commands manually:\n\n"
        "   Option 1 (recommended):\n"
        "     sudo playwright install-deps chromium\n\n"
        "   Option 2 (apt-get on Debian/Ubuntu):\n"
        "     sudo apt-get update && sudo apt-get install -y libnspr4 libnss3 libasound2t64\n\n"
        "   Option 3 (if libasound2t64 not found):\n"
        "     sudo apt-get update && sudo apt-get install -y libnspr4 libnss3 libasound2"
    )
    return False, instructions


def ensure_playwright_browsers() -> tuple[bool, str | None]:
    """
    Ensure Playwright browsers are installed and working. Called lazily on first tool use.
    
    This function:
    1. Checks if playwright module is installed
    2. Checks if browsers are already installed (fast path)
    3. If not, attempts to install them automatically
    4. On Linux, also installs system dependencies if needed
    
    Returns:
        Tuple of (success: bool, error_message: str | None)
    """
    global _playwright_install_attempted, _playwright_browsers_available
    
    # Return cached result if we've already tried
    if _playwright_install_attempted:
        if _playwright_browsers_available:
            return True, None
        return False, "Playwright browsers installation previously failed. Run: playwright install chromium"
    
    _playwright_install_attempted = True
    
    # First check if playwright module is available
    try:
        import playwright  # noqa: F401
    except ImportError:
        _playwright_browsers_available = False
        return False, (
            "Playwright is not installed. Install with:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )
    
    # Check if browsers are already installed AND can launch (fast path)
    if _check_playwright_browsers_installed():
        can_launch, launch_error = _check_playwright_can_launch()
        if can_launch:
            logger.debug("Playwright Chromium browser already installed and working")
            _playwright_browsers_available = True
            return True, None
        elif launch_error == "system_deps":
            # Browsers installed but system deps missing (Linux)
            logger.info("Playwright browsers installed but system dependencies missing")
            success, msg = _install_playwright_system_deps()
            if success:
                _playwright_browsers_available = True
                return True, None
            else:
                _playwright_browsers_available = False
                return False, msg
    
    # Try to install browsers
    logger.info("🔧 Installing Playwright Chromium browser (first-time setup)...")
    logger.info("   This may take a few minutes...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout for slow connections
        )
        logger.info("✅ Playwright Chromium browser installed successfully")
        
        # On Linux, also install system dependencies
        if platform.system().lower() == "linux":
            can_launch, launch_error = _check_playwright_can_launch()
            if not can_launch and launch_error == "system_deps":
                success, msg = _install_playwright_system_deps()
                if not success:
                    _playwright_browsers_available = False
                    return False, msg
        
        _playwright_browsers_available = True
        return True, None
    except subprocess.CalledProcessError as e:
        error_output = e.stderr or e.stdout or str(e)
        # Check for common errors
        if "PLAYWRIGHT_BROWSERS_PATH" in error_output:
            error_msg = (
                "Playwright browser installation failed due to path issues.\n"
                "Try setting PLAYWRIGHT_BROWSERS_PATH environment variable.\n"
                f"Details: {error_output[:200]}"
            )
        elif "permission" in error_output.lower():
            error_msg = (
                "Playwright browser installation failed due to permission issues.\n"
                "Try running: playwright install chromium\n"
                f"Details: {error_output[:200]}"
            )
        else:
            error_msg = f"Could not install Playwright Chromium: {error_output[:300]}"
        
        logger.warning(f"⚠️  {error_msg}")
        _playwright_browsers_available = False
        return False, f"{error_msg}\nPlease run manually: playwright install chromium"
    except subprocess.TimeoutExpired:
        error_msg = "Playwright installation timed out (>10 minutes)"
        logger.warning(f"⚠️  {error_msg}")
        _playwright_browsers_available = False
        return False, f"{error_msg}\nPlease run manually: playwright install chromium"
    except FileNotFoundError:
        _playwright_browsers_available = False
        return False, (
            "Playwright command not found. Install with:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )
    except Exception as e:
        error_msg = f"Unexpected error during Playwright installation: {e}"
        logger.warning(f"⚠️  {error_msg}")
        _playwright_browsers_available = False
        return False, f"{error_msg}\nPlease run manually: playwright install chromium"


def _check_deno_installed() -> bool:
    """Check if Deno is already installed and accessible."""
    try:
        result = subprocess.run(
            ["deno", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    except Exception:
        return False


def _get_deno_install_command() -> tuple[list[str], str]:
    """
    Get the appropriate Deno installation command for the current OS.
    
    Returns:
        Tuple of (command_args, shell_type) where shell_type is used for shell=True on Windows
    """
    system = platform.system().lower()
    
    if system == "windows":
        # Windows: Use PowerShell to install Deno
        return (
            ["powershell", "-Command", 
             "irm https://deno.land/install.ps1 | iex"],
            "powershell"
        )
    elif system == "darwin":
        # macOS: Use curl with shell script
        return (
            ["sh", "-c", "curl -fsSL https://deno.land/install.sh | sh"],
            "sh"
        )
    elif system == "linux":
        # Linux: Use curl with DENO_INSTALL set
        home = Path.home()
        deno_install_dir = home / ".deno"
        install_script = (
            f"export DENO_INSTALL=\"{deno_install_dir}\" && "
            "curl -fsSL https://deno.land/install.sh | sh"
        )
        return (
            ["bash", "-c", install_script],
            "bash"
        )


def _ensure_curl_and_unzip_installed() -> bool:
    """Ensure curl and unzip are installed on Linux, attempt to install if not."""
    system = platform.system().lower()
    if system != "linux":
        return True
    
    curl_ok = shutil.which("curl") is not None
    unzip_ok = shutil.which("unzip") is not None
    
    if curl_ok and unzip_ok:
        return True
    
    missing = []
    if not curl_ok:
        missing.append("curl")
    if not unzip_ok:
        missing.append("unzip")
    
    logger.info(f"   {', '.join(missing)} not found, attempting to install...")
    sudo = _sudo_prefix()
    
    try:
        # Try apt-get (Debian/Ubuntu)
        subprocess.run(
            sudo + ["apt-get", "update"],
            capture_output=True,
            timeout=60
        )
        result = subprocess.run(
            sudo + ["apt-get", "install", "-y"] + missing,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            logger.info(f"   ✅ {', '.join(missing)} installed successfully")
            return True
    except Exception:
        pass
    
    # Try yum (RHEL/CentOS)
    try:
        result = subprocess.run(
            sudo + ["yum", "install", "-y"] + missing,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            logger.info(f"   ✅ {', '.join(missing)} installed successfully")
            return True
    except Exception:
        pass
    
    logger.warning(f"   Could not install {', '.join(missing)} automatically")
    return False


def _get_deno_manual_install_instructions() -> str:
    """Get manual installation instructions for Deno."""
    system = platform.system().lower()
    
    if system == "windows":
        return (
            "Install Deno manually:\n"
            "  PowerShell: irm https://deno.land/install.ps1 | iex\n"
            "  Or with Chocolatey: choco install deno\n"
            "  Or with Scoop: scoop install deno"
        )
    elif system == "linux":
        return (
            "Install Deno manually:\n"
            "  curl -fsSL https://deno.land/install.sh | sh\n\n"
            "  If curl is not installed:\n"
            "    sudo apt-get update && sudo apt-get install -y curl\n"
            "    Then run the curl command above\n\n"
            "  Or with Snap: sudo snap install deno\n\n"
            "  After installation, add to PATH:\n"
            "    echo 'export PATH=\"$HOME/.deno/bin:$PATH\"' >> ~/.bashrc\n"
            "    source ~/.bashrc"
        )
    else:
        return (
            "Install Deno manually:\n"
            "  curl -fsSL https://deno.land/install.sh | sh\n\n"
            "  After installation, add to PATH:\n"
            "    echo 'export PATH=\"$HOME/.deno/bin:$PATH\"' >> ~/.zshrc\n"
            "    source ~/.zshrc"
        )


def _get_deno_path_instructions() -> str:
    """Get instructions for adding Deno to PATH based on OS."""
    system = platform.system().lower()
    home = Path.home()
    
    if system == "windows":
        deno_path = home / ".deno" / "bin"
        return (
            f"Add Deno to your PATH:\n"
            f"  1. Open System Properties > Environment Variables\n"
            f"  2. Add '{deno_path}' to your PATH\n"
            f"  Or run in PowerShell: $env:PATH += ';{deno_path}'"
        )
    else:
        deno_path = home / ".deno" / "bin"
        shell_config = ".bashrc" if system == "linux" else ".zshrc"
        return (
            f"Add Deno to your PATH:\n"
            f"  echo 'export PATH=\"{deno_path}:$PATH\"' >> ~/{shell_config}\n"
            f"  source ~/{shell_config}\n"
            f"  Or for current session: export PATH=\"{deno_path}:$PATH\""
        )


def ensure_deno() -> tuple[bool, str | None, str | None]:
    """
    Ensure Deno runtime is installed. Called lazily when MCP servers need it.

    This function:
    1. Checks if deno is already installed and in PATH
    2. If not, attempts to install it automatically
    3. Provides OS-specific installation and PATH instructions

    Returns:
        Tuple of (success: bool, error_message: str | None, deno_path: str | None)
        - success: True if deno is available
        - error_message: Error or warning message (can be present even with success=True)
        - deno_path: Command to use ('deno' if in PATH, or absolute path to binary)
    """
    global _deno_install_attempted, _deno_available, _deno_path

    # Return cached result if we've already tried
    if _deno_install_attempted:
        if _deno_available:
            return True, None, _deno_path
        return False, "Deno installation previously failed. Install manually from https://deno.land", None

    _deno_install_attempted = True

    # Check if deno is already installed (fast path)
    if _check_deno_installed():
        logger.debug("Deno is already installed")
        _deno_available = True
        _deno_path = "deno"
        return True, None, "deno"

    # Also check common installation paths
    home = Path.home()
    deno_bin = home / ".deno" / "bin" / ("deno.exe" if platform.system() == "Windows" else "deno")
    if deno_bin.exists():
        logger.info(f"Deno found at {deno_bin} but not in PATH")
        _deno_available = True
        _deno_path = str(deno_bin)
        path_instructions = _get_deno_path_instructions()
        return True, f"Deno is installed but not in PATH.\n{path_instructions}", str(deno_bin)
    
    # Try to install Deno
    logger.info("🔧 Installing Deno runtime (first-time setup)...")
    logger.info("   This may take a minute...")
    
    system = platform.system().lower()
    
    # On Linux, ensure curl and unzip are available first
    if system == "linux":
        _ensure_curl_and_unzip_installed()
    
    try:
        cmd, shell_type = _get_deno_install_command()
        
        # Set up environment with HOME for the installer
        env = os.environ.copy()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            env=env
        )
        
        if result.returncode == 0:
            # Verify installation
            if deno_bin.exists() or _check_deno_installed():
                logger.info("✅ Deno installed successfully")
                _deno_available = True

                # Check if it's in PATH
                if not _check_deno_installed():
                    _deno_path = str(deno_bin)
                    path_instructions = _get_deno_path_instructions()
                    return True, f"Deno installed successfully!\n{path_instructions}", str(deno_bin)
                else:
                    _deno_path = "deno"
                    return True, None, "deno"
            else:
                error_msg = "Deno installation completed but binary not found"
                logger.warning(f"⚠️  {error_msg}")
                _deno_available = False
                return False, f"{error_msg}\nInstall manually: https://deno.land", None
        else:
            error_output = result.stderr or result.stdout or "Unknown error"
            error_msg = f"Deno installation failed: {error_output[:300]}"
            logger.warning(f"⚠️  {error_msg}")
            _deno_available = False
            return False, f"{error_msg}\nInstall manually: https://deno.land", None

    except subprocess.TimeoutExpired:
        error_msg = "Deno installation timed out (>5 minutes)"
        logger.warning(f"⚠️  {error_msg}")
        _deno_available = False
        return False, f"{error_msg}\nInstall manually: https://deno.land", None
    except FileNotFoundError as e:
        manual_instructions = _get_deno_manual_install_instructions()
        if system == "windows":
            error_msg = f"PowerShell not found.\n\n{manual_instructions}"
        else:
            error_msg = f"curl or bash not found.\n\n{manual_instructions}"
        logger.warning(f"⚠️  {error_msg}")
        _deno_available = False
        return False, error_msg, None
    except Exception as e:
        manual_instructions = _get_deno_manual_install_instructions()
        error_msg = f"Unexpected error during Deno installation: {e}\n\n{manual_instructions}"
        logger.warning(f"⚠️  {error_msg}")
        _deno_available = False
        return False, error_msg, None


def get_deno_command() -> str:
    """
    Get the Deno command to use for MCP servers.

    This function ensures Deno is installed and returns the appropriate command:
    - "deno" if it's in the system PATH
    - Absolute path to the Deno binary if it's installed but not in PATH

    This allows MCP servers to work seamlessly regardless of whether the user
    has added Deno to their PATH.

    Returns:
        str: The command to use to run Deno ("deno" or absolute path)

    Example:
        >>> from agent_framework.utils import get_deno_command
        >>>
        >>> # In your MCP configuration
        >>> mcp_config = {
        >>>     "command": get_deno_command(),
        >>>     "args": ["run", "-N", "jsr:@pydantic/mcp-run-python", "stdio"]
        >>> }
    """
    success, message, deno_path = ensure_deno()

    if success and deno_path:
        return deno_path

    # Fallback to "deno" if something went wrong
    # (the MCP server will fail later with a clear error message)
    logger.warning("Could not determine Deno path, falling back to 'deno' command")
    return "deno"


def post_install():
    """Install all required dependencies after package installation"""
    # Configure logging for CLI usage
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    all_success = True
    system = platform.system().lower()
    
    # Install Playwright browsers
    print("=" * 50)
    print("Installing Playwright browsers...")
    print("=" * 50)
    success, error = ensure_playwright_browsers()
    if not success:
        print(f"Warning: {error}", file=sys.stderr)
        all_success = False
    else:
        print("✅ Playwright Chromium browser ready")
    
    # On Linux, remind about system dependencies
    if system == "linux":
        print()
        print("📋 Note for Linux users:")
        print("   If you encounter browser launch errors, run:")
        print("   sudo playwright install-deps chromium")
    
    # Install Deno
    print()
    print("=" * 50)
    print("Installing Deno runtime...")
    print("=" * 50)
    success, message, deno_path = ensure_deno()
    if not success:
        print(f"Warning: {message}", file=sys.stderr)
        all_success = False
    elif message:
        # Success but with a message (e.g., PATH instructions)
        print(message)
        print(f"✅ Deno runtime ready (path: {deno_path})")
    else:
        print(f"✅ Deno runtime ready (command: {deno_path})")
    
    print()
    print("=" * 50)
    if all_success:
        print("✅ All dependencies installed successfully!")
    else:
        print("⚠️  Some dependencies could not be installed automatically.")
        print("   See warnings above for manual installation instructions.")
    print("=" * 50)
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(post_install())
