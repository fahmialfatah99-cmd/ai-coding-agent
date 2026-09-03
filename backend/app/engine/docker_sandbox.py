import os
import sys
import subprocess
from typing import Dict, Any, Optional

try:
    import docker
    HAS_DOCKER_LIB = True
except ImportError:
    HAS_DOCKER_LIB = False


class DockerSandboxManager:
    """
    Cross-Platform Sandbox Environment Manager (Linux / Windows / Docker).
    Runs commands in an isolated Docker container with memory & CPU constraints,
    with robust local fallback supporting PowerShell on Windows and bash on Linux.
    """
    
    def __init__(
        self,
        workspace_path: str,
        container_image: str = "python:3.11-slim",
        mem_limit: str = "512m",
        cpu_quota: float = 1.0
    ):
        self.workspace_path = os.path.abspath(workspace_path)
        os.makedirs(self.workspace_path, exist_ok=True)
        
        self.container_image = container_image
        self.mem_limit = mem_limit
        self.cpu_quota = cpu_quota
        self.container = None
        self.docker_client = None
        
        if HAS_DOCKER_LIB and not os.path.exists("/.dockerenv"):
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
            except Exception:
                self.docker_client = None
        else:
            self.docker_client = None

    def start_sandbox(self) -> Optional[str]:
        """Starts the isolated container if Docker is available."""
        if not self.docker_client:
            return None

        try:
            self.container = self.docker_client.containers.run(
                self.container_image,
                command="/bin/sh -c 'tail -f /dev/null'",
                volumes={self.workspace_path: {"bind": "/workspace", "mode": "rw"}},
                working_dir="/workspace",
                detach=True,
                mem_limit=self.mem_limit,
                nano_cpus=int(self.cpu_quota * 1_000_000_000),
                network_mode="bridge",
                pids_limit=100
            )
            return self.container.id
        except Exception:
            self.container = None
            return None

    def execute_command(self, cmd: str, timeout_sec: int = 30) -> Dict[str, Any]:
        """
        Executes a shell command inside the sandbox container or local fallback.
        """
        # 1. Try Docker Container execution
        if self.docker_client:
            if not self.container:
                self.start_sandbox()

            if self.container:
                try:
                    exec_res = self.container.exec_run(
                        cmd=["/bin/sh", "-c", cmd],
                        workdir="/workspace",
                        demux=True,
                        environment={"PYTHONUNBUFFERED": "1"}
                    )
                    stdout = exec_res.output[0].decode("utf8", errors="replace") if exec_res.output[0] else ""
                    stderr = exec_res.output[1].decode("utf8", errors="replace") if exec_res.output[1] else ""

                    return {
                        "exit_code": exec_res.exit_code,
                        "stdout": stdout,
                        "stderr": stderr,
                        "success": exec_res.exit_code == 0,
                        "environment": "docker_sandbox"
                    }
                except Exception:
                    pass

        # 2. Local Subprocess Fallback
        return self._run_local_fallback(cmd, timeout_sec)

    def _get_execution_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        try:
            import glob
            user_nvm = os.path.expanduser("~/.nvm/versions/node/*/bin")
            nvm_nodes = glob.glob(user_nvm) + glob.glob('/root/.nvm/versions/node/*/bin')
            if nvm_nodes:
                env['PATH'] = ':'.join(nvm_nodes) + ':' + env.get('PATH', '')
        except Exception:
            pass
        return env

    def execute_command_argv(self, argv, timeout_sec: int = 30) -> Dict[str, Any]:
        """
        Executes a command as an argument vector (no shell interpolation).
        This is the SAFE path for any user-influenced input such as git commit
        messages, branch names, or file paths — shell metacharacters cannot
        break out into arbitrary command execution.

        The argv is a list of strings, e.g. ["git", "commit", "-m", "..."].
        On Docker we pass the list directly to exec_run; on local fallback we
        run it via subprocess.run with shell=False.
        """
        if not argv or not isinstance(argv, (list, tuple)) or not all(isinstance(a, str) for a in argv):
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "execute_command_argv requires a list of strings.",
                "success": False,
                "environment": "error",
            }

        # 1. Try Docker Container execution (no shell).
        if self.docker_client:
            if not self.container:
                self.start_sandbox()
            if self.container:
                try:
                    exec_res = self.container.exec_run(
                        cmd=list(argv),
                        workdir="/workspace",
                        demux=True,
                        environment={"PYTHONUNBUFFERED": "1"},
                    )
                    stdout = exec_res.output[0].decode("utf8", errors="replace") if exec_res.output[0] else ""
                    stderr = exec_res.output[1].decode("utf8", errors="replace") if exec_res.output[1] else ""
                    return {
                        "exit_code": exec_res.exit_code,
                        "stdout": stdout,
                        "stderr": stderr,
                        "success": exec_res.exit_code == 0,
                        "environment": "docker_sandbox",
                    }
                except Exception:
                    pass

        # 2. Local Subprocess Fallback (shell=False).
        try:
            env = self._get_execution_env()
            if os.name == "nt":
                res = subprocess.run(
                    list(argv),
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    env=env,
                )
            else:
                res = subprocess.run(
                    list(argv),
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    env=env,
                )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout or "",
                "stderr": res.stderr or "",
                "success": res.returncode == 0,
                "environment": "local_fallback",
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_sec} seconds.",
                "success": False,
                "environment": "local_fallback",
            }
        except FileNotFoundError as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command not found: {e}",
                "success": False,
                "environment": "local_fallback",
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution Error: {str(e)}",
                "success": False,
                "environment": "local_fallback",
            }

    def _run_local_fallback(self, cmd: str, timeout_sec: int) -> Dict[str, Any]:
        try:
            if os.name == "nt":
                # Use PowerShell with compatibility aliases for POSIX commands (head, tail, touch, rm -rf, etc.)
                compat_preamble = "function head { param([int]$n=10) $input | Select-Object -First $n }; function tail { param([int]$n=10) $input | Select-Object -Last $n }; "
                args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", compat_preamble + cmd]
                res = subprocess.run(
                    args,
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    env=self._get_execution_env()
                )
            else:
                env = self._get_execution_env()
                res = subprocess.run(
                    cmd,
                    shell=True,
                    executable="/bin/bash",
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    env=env
                )

            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "success": res.returncode == 0,
                "environment": "local_fallback"
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_sec} seconds.",
                "success": False,
                "environment": "local_fallback"
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution Error: {str(e)}",
                "success": False,
                "environment": "local_fallback"
            }

    def cleanup(self):
        """Stops and removes running container."""
        if self.container:
            try:
                self.container.stop(timeout=2)
                self.container.remove(force=True)
            except Exception:
                pass
            finally:
                self.container = None
