"""
Node.js bridge - executes SDK via subprocess instead of PythonMonkey.
This avoids PythonMonkey's Node.js built-in limitations.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .exceptions import VortexSDKError


class NodeBridge:
    """Bridge to execute Vortex SDK via Node.js subprocess."""

    def __init__(self, sdk_config: Dict[str, Any]):
        """Initialize the Node.js bridge."""
        self.sdk_config = sdk_config
        self._verify_node()
        self._find_sdk()

    def _verify_node(self) -> None:
        """Verify Node.js is available."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            # Check version is 18+
            major = int(version.lstrip('v').split('.')[0])
            if major < 18:
                raise VortexSDKError(f"Node.js 18+ required, found {version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise VortexSDKError(
                "Node.js 18+ is required but not found. "
                "Install from https://nodejs.org/"
            )

    def _find_sdk(self) -> None:
        """Find the npm-installed SDK (local or global)."""
        # First check local node_modules in current working directory
        sdk_path = Path.cwd() / "node_modules" / "@vortexfi" / "sdk"

        if sdk_path.exists():
            return  # Local installation found

        # Check if Node.js can require it (works for global installs too)
        try:
            test_script = """
            try {
                require.resolve('@vortexfi/sdk');
                console.log('OK');
            } catch (e) {
                process.exit(1);
            }
            """
            result = subprocess.run(
                ["node", "-e", test_script],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip() == "OK":
                return  # SDK is accessible to Node.js (global or local)
        except Exception:
            pass

        # SDK not found anywhere
        raise VortexSDKError(
            "@vortexfi/sdk not found. Install it with:\n"
            "  npm install @vortexfi/sdk  (local install)\n"
            "  npm install -g @vortexfi/sdk  (global install)"
        )

    def call_method(self, method: str, *args, timeout: int = 60) -> Any:
        """Call a SDK method via Node.js.

        Args:
            method: SDK method name
            *args: Method arguments
            timeout: Timeout in seconds (default 60, use higher for registerRamp)
        """
        script = f"""
        import {{ VortexSdk }} from "@vortexfi/sdk";
        (async () => {{
            try {{
                // Redirect console.log to stderr to keep stdout clean for JSON only
                const originalLog = console.log;
                console.log = (...args) => console.error(...args);

                const config = {json.dumps(self.sdk_config)};
                const sdk = new VortexSdk(config);

                const methodArgs = {json.dumps(args)};

                const result = await sdk.{method}(...methodArgs);

                // Restore console.log and output JSON to stdout
                console.log = originalLog;
                console.log(JSON.stringify({{ success: true, result }}));
                process.exit(0);
            }} catch (error) {{
                console.error(JSON.stringify({{
                    success: false,
                    error: error.message,
                    stack: error.stack
                }}));
                process.exit(1);
            }}
        }})();
        """

        try:
            result = subprocess.run(
                ["node", "--input-type=module", "-e", script],
                capture_output=True,
                text=True,
                check=False,
                cwd=str(Path.cwd()),
                timeout=timeout
            )

            # Check for errors in stderr
            if result.stderr:
                # Try to parse as JSON error first
                stderr_lines = result.stderr.strip().split('\n')
                for line in reversed(stderr_lines):
                    if line.startswith('{'):
                        try:
                            error_data = json.loads(line)
                            if not error_data.get('success', True):
                                error_msg = error_data.get('error', 'Unknown error')
                                stack = error_data.get('stack', '')
                                raise VortexSDKError(
                                    f"SDK error: {error_msg}\n"
                                    f"Stack trace:\n{stack}"
                                )
                        except json.JSONDecodeError:
                            pass

                # If returncode is non-zero, treat stderr as error
                if result.returncode != 0:
                    raise VortexSDKError(
                        f"Node.js process failed (exit code {result.returncode}):\n{result.stderr}"
                    )

            if not result.stdout:
                raise VortexSDKError(
                    f"No output from Node.js process.\n"
                    f"Exit code: {result.returncode}\n"
                    f"stderr output:\n{result.stderr or '(empty)'}"
                )

            # Try to find JSON in stdout (last line that starts with {)
            stdout_lines = result.stdout.strip().split('\n')
            json_line = None
            for line in reversed(stdout_lines):
                if line.strip().startswith('{'):
                    json_line = line
                    break

            if not json_line:
                raise VortexSDKError(
                    f"No JSON response found in stdout.\n"
                    f"stdout output:\n{result.stdout[:1000]}\n"
                    f"stderr output:\n{result.stderr[:500] if result.stderr else '(empty)'}"
                )

            response = json.loads(json_line)
            if not response.get('success'):
                error_msg = response.get('error', 'Unknown error')
                raise VortexSDKError(f"SDK error: {error_msg}")

            return response['result']

        except subprocess.TimeoutExpired:
            raise VortexSDKError(
                f"SDK call '{method}' timed out after {timeout}s. "
                "This may be due to network initialization or blockchain operations. "
                "Check your network connectivity and RPC URLs."
            )
        except json.JSONDecodeError as e:
            raise VortexSDKError(
                f"Failed to parse response. "
                f"stdout: {result.stdout[:500] if result.stdout else '(empty)'}, "
                f"stderr: {result.stderr[:500] if result.stderr else '(empty)'}"
            )
        except Exception as e:
            if isinstance(e, VortexSDKError):
                raise
            raise VortexSDKError(f"Bridge error: {str(e)}") from e
