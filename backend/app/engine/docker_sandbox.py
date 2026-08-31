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
        
        if HAS_DOCKER_LIB:
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
            except Exception:
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

    def _run_local_fallback(self, cmd: str, timeout_sec: int) -> Dict[str, Any]:
        try:
            if os.name == "nt":
                # Use PowerShell on Windows for POSIX compatibility (mkdir -p, python -c, ls, etc.)
                args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd]
                res = subprocess.run(
                    args,
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec
                )
            else:
                res = subprocess.run(
                    cmd,
                    shell=True,
                    executable="/bin/bash",
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec
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
