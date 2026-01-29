from typing import Optional
from agno.agent import Agent
from agno.tools import Toolkit
import subprocess
import tempfile
import os

class ChunkedShellTools(Toolkit):
    def __init__(self, chunk_size: int = 2000, working_dir: str = None):
        self.chunk_size = chunk_size
        self.working_dir = working_dir or os.getcwd()
        self._output_cache = {}  # Store outputs by command hash

        super().__init__(
            name="chunked_shell_tools",
            tools=[
                self.run_shell_command,
                self.read_output_chunk,
                self.get_output_info,
            ]
        )

    def run_shell_command(self, command: str) -> str:
        """Execute a shell command. If output is long, returns first chunk and info to read more.

        Args:
            command: The shell command to execute
        Returns:
            First chunk of output or full output if short
        """
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=self.working_dir)
        output = result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

        cmd_id = str(hash(command))[:8]
        self._output_cache[cmd_id] = output

        if len(output) <= self.chunk_size:
            return output

        total_chunks = (len(output) + self.chunk_size - 1) // self.chunk_size
        return f"[Output too long: {len(output)} chars, {total_chunks} chunks]\n\nChunk 1/{total_chunks}:\n{output[:self.chunk_size]}\n\n[Use read_output_chunk('{cmd_id}', chunk_num) to read more]"

    def read_output_chunk(self, cmd_id: str, chunk_num: int) -> str:
        """Read a specific chunk of a previous command's output.

        Args:
            cmd_id: The command ID from run_shell_command
            chunk_num: Chunk number (1-indexed)
        """
        if cmd_id not in self._output_cache:
            return f"Error: No cached output for command ID '{cmd_id}'"

        output = self._output_cache[cmd_id]
        start = (chunk_num - 1) * self.chunk_size
        end = start + self.chunk_size
        total_chunks = (len(output) + self.chunk_size - 1) // self.chunk_size

        return f"Chunk {chunk_num}/{total_chunks}:\n{output[start:end]}"

    def get_output_info(self, cmd_id: str) -> str:
        """Get info about cached command output."""
        if cmd_id not in self._output_cache:
            return f"No cached output for '{cmd_id}'"
        output = self._output_cache[cmd_id]
        total_chunks = (len(output) + self.chunk_size - 1) // self.chunk_size
        return f"Total length: {len(output)} chars, {total_chunks} chunks available"

# Usage
# agent = Agent(tools=[ChunkedShellTools(chunk_size=2000)])
# agent.print_response("Run 'find / -name *.py' and summarize the results")
