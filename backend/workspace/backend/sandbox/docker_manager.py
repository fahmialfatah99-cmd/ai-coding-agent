"""
Secure Sandbox Manager untuk eksekusi kode terisolasi.
"""
import asyncio
import subprocess

class SandboxManager:
    """
    Wrapper untuk eksekusi perintah di dalam Docker container atau E2B sandbox.
    """
    def __init__(self, container_id: str = "ai-agent-sandbox"):
        self.container_id = container_id

    async def execute(self, command: str, workspace_path: str) -> str:
        """
        Menjalankan perintah shell di dalam container.
        """
        # Dalam implementasi nyata, gunakan docker SDK atau E2B SDK
        # Contoh: docker exec -w /workspace <container_id> <command>
        
        print(f"Executing in sandbox: {command}")
        
        # Simulasi eksekusi (menggunakan subprocess lokal untuk demo)
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace_path
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode()
            error = stderr.decode()
            
            if process.returncode != 0:
                return f"Error (Exit Code {process.returncode}):\n{error}"
            
            return output if output else "Command executed successfully (no output)."
        except Exception as e:
            return f"Sandbox Execution Failed: {str(e)}"
