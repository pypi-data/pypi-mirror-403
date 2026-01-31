"""gemini cli agent plugin for familiar"""

from __future__ import annotations

import subprocess
from pathlib import Path

from familiar.agents import Agent


class GeminiAgent(Agent):
    """agent that uses the gemini cli"""

    name = "gemini"
    output_file = "GEMINI.md"

    def run(
        self, repo_root: Path, prompt: str, headless: bool, auto: bool = False
    ) -> int:
        cmd = ["gemini"]
        if auto:
            cmd.append("--approval-mode=yolo")
        if headless:
            cmd.extend(["-p", prompt])
        else:
            cmd.extend(["-i", prompt])
        return subprocess.call(cmd, cwd=repo_root)
