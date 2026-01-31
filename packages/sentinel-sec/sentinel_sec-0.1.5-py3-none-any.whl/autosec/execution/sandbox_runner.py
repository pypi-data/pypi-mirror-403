import docker
import os
import tarfile
import io
import logging
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SandboxRunner:
    def __init__(self, image: str = "python:3.10-slim"):
        self.image = image
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def _create_tar_stream(self, file_content: str, filename: str) -> io.BytesIO:
        """Creates a tar stream for a single file to copy into the container."""
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            data = file_content.encode('utf-8')
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(data)
            tar.addfile(tarinfo, io.BytesIO(data))
        tar_stream.seek(0)
        return tar_stream

    def run_test(
        self, 
        repo_path: str, 
        patch_content: str, 
        test_command: str = "pytest",
        target_file_rel_path: str = "patch_target.py", # This needs to be dynamic in real usage
        timeout: int = 30
    ) -> Tuple[str, str, int]:
        """
        Runs the tests in an ephemeral container.
        
        Args:
            repo_path: Absolute path to the repository on host.
            patch_content: The new code content to test.
            test_command: Command to run tests.
            target_file_rel_path: Relative path in the repo where the patch applies.
            timeout: Execution timeout in seconds.
            
        Returns:
            stdout, stderr, exit_code
        """
        if not self.client:
            return "", "Docker client not initialized", -1

        container = None
        try:
            # 1. Spin up container
            # We mount the repo as read-only to /app/src
            # We use a tmp volume or directory for the writable execution space if needed, 
            # OR we just copy everything to a writable dir inside.
            # Strategy:
            # - Mount local repo to /host_repo (ro)
            # - Command: cp -r /host_repo /app && apply patch && run tests
            
            logger.info("Spawning container...")
            container = self.client.containers.run(
                self.image,
                command="sleep infinity", # Keep alive to exec commands
                detach=True,
                network_disabled=True,
                mem_limit="512m",
                # pids_limit=64, # SDK might not support this directly in all versions, checking docs is good
                # read_only=True, # We need to write to /app, so rootfs ro might be too strict unless we use volumes
                working_dir="/app",
                volumes={
                    repo_path: {'bind': '/host_repo', 'mode': 'ro'}
                }
            )

            # 2. Setup: Copy repo from read-only mount to writable /app
            # Note: 'cp' must exist in the image. python:slim usually has basic coreutils.
            setup_cmd = "cp -r /host_repo/. /app"
            exit_code, output = container.exec_run(f"sh -c '{setup_cmd}'")
            if exit_code != 0:
                logger.error(f"Setup failed: {output.decode()}")
                return output.decode(), "Setup failed", exit_code

            # 3. Apply Patch
            # We overwrite the specific file with the patch content
            # docker put_archive is the way to write files
            tar_stream = self._create_tar_stream(patch_content, target_file_rel_path)
            # target_file_rel_path e.g., "src/vuln.py". We need to handle directory structure in tar? 
            # Simplified: assuming flat or exact path provided.
            # For this MVP, let's assume valid relative path.
            
            # Note: put_archive extracts to the 'path'. 
            # If path is /app, and tar contains 'src/vuln.py', it goes to /app/src/vuln.py
            
            # We need to construct the tar correctly with full directory structure?
            # Or just overwrite.
            
            logger.info("Applying patch...")
            container.put_archive(path="/app", data=tar_stream)
            
            # 4. Run Test
            logger.info(f"Running tests: {test_command}")
            # We wrap in sh -c to ensure environment variables etc?
            exec_result = container.exec_run(
                f"sh -c '{test_command}'",
                workdir="/app"
            )
            
            stdout = exec_result.output.decode('utf-8')
            stderr = "" # exec_run combines stdout/stderr usually, or we can demultiplex
            exit_code = exec_result.exit_code
            
            return stdout, stderr, exit_code

        except Exception as e:
            logger.exception("Sandbox execution error")
            return "", str(e), -1
        finally:
            if container:
                logger.info("Killing container...")
                try:
                    container.kill()
                    container.remove()
                except Exception:
                    pass

if __name__ == "__main__":
    # Test stub
    print("Sandbox Runner initialized.")
