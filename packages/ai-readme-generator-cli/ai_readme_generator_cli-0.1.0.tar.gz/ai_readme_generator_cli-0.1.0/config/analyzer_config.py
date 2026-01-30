
from typing import Any
from pydantic import BaseModel



class AnalyzerConfigFile(BaseModel): 
        # Dirs or Files which will not be included irrespective of their path
        global_ignore: list[str] = [
                "__pycache__"
        ]
        # Folders will not be included in analyzing code. Dirs Path is relative to root
        ignore_dirs: list[str] = [
                "node_modules",
                "__pycache__",
                ".git",
                ".idea",
                ".vscode",
                "config"
        ]
        # Extension wil not be included in analyzing code
        ignore_extensions: list[str] = [
                ".log",
                ".lock",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".zip",
                ".exe"
        ]
        # Files will not be included in analyzing code. File Path is relative to root
        ignore_files: list[str] = [
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
                "poetry.lock",
                "Pipfile.lock",
                "Cargo.lock"
        ]
        # Directories/Sub-Directories that MUST be included even if ignored by rules above (write full path from projectroot)
        include_dirs: list[str]= [
               
        ]
        # Files that MUST be included even if ignored by rules above (write full path from projectroot)
        include_files: list[str]= [
               
        ]

        llm: dict[str, Any] = {
                "key": "",
                "model_provider": "OPENAI",
                "model": "gpt-4o-mini",
                "batch_limit": 100000,
                "temperature": 0.7
        }

