import logging
import requests
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("go-judge.client")

class RemoteSandbox:
    """
    Client for interacting with a running go-judge server via HTTP.
    """
    
    # Language Configuration moved here
    DEFAULT_LANG_CONFIG = {
        "cpp": {
            "src_name": "a.cc",
            "bin_name": "a",
            "compile": {
                "args": ["/usr/bin/g++", "a.cc", "-o", "a"],
                "env": ["PATH=/usr/bin:/bin"]
            },
            "run": {
                "args": ["./a"],
                "env": ["PATH=/usr/bin:/bin"]
            }
        },
        "python": {
            "src_name": "solution.py",
            "bin_name": None,
            "compile": None,
            "run": {
                "args": ["/usr/bin/python3", "solution.py"],
                "env": ["PATH=/usr/bin:/bin", "PYTHONPATH=/usr/lib/python3.11"]
            }
        },
    }

    def __init__(self, api_url: str, custom_languages: Dict[str, Any] = None, max_workers: int = 16):
        """
        Args:
            api_url: Base URL of the go-judge server.
            custom_languages: Dictionary to merge with or override defaults.
            max_workers: Number of threads to use for parallel execution.
        """
        self.api_url = api_url.rstrip("/")
        self.languages = self.DEFAULT_LANG_CONFIG.copy()
        if custom_languages:
            self.languages.update(custom_languages)

        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def close(self):
        """Shuts down the internal thread pool."""
        logger.info("Shutting down client executor...")
        self._executor.shutdown(wait=True)

    def register_language(self, name: str, config: Dict[str, Any]):
        """
        Registers a new language or overwrites an existing one dynamically.
        
        Args:
            name: Identifier (e.g., "rust", "cpp-O3")
            config: The configuration dictionary containing src_name, run, compile, etc.
        """
        self.languages[name] = config
        logger.info(f"Registered language configuration for '{name}'")

    def check_health(self) -> bool:
        """Checks if the server is responsive."""
        try:
            requests.get(f"{self.api_url}/version", timeout=1)
            return True
        except requests.RequestException:
            return False

    def cleanup_file(self, file_id: str):
        """Deletes a cached file from the sandbox memory."""
        try:
            requests.delete(f"{self.api_url}/file/{file_id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_id}: {e}")

    def run(
        self, 
        language: str, 
        code: str, 
        input: str = "", 
        # Default: 5s / 256MB for Execution
        exec_cpu_limit_ns: int = 5_000_000_000, 
        exec_memory_limit_b: int = 268_435_456,
        # Default: 30s / 512MB for Compilation
        compile_cpu_limit_ns: int = 30_000_000_000,
        compile_memory_limit_b: int = 536_870_912,
    ) -> Dict[str, Any]:
        """
        Runs code with a single input.
        """
        # We simply wrap the single input in a list and return the first result
        results = self.run_multiple(
            language, code, [input],
            exec_cpu_limit_ns, exec_memory_limit_b,
            compile_cpu_limit_ns, compile_memory_limit_b
        )
        return results[0]

    def run_multiple(
        self,
        language: str,
        code: str,
        inputs: List[str],
        exec_cpu_limit_ns: int = 5_000_000_000, 
        exec_memory_limit_b: int = 268_435_456,
        compile_cpu_limit_ns: int = 30_000_000_000,
        compile_memory_limit_b: int = 536_870_912,
    ) -> List[Dict[str, Any]]:
        """
        Compiles (if needed) and runs the code against the remote server.
        """
        if language not in self.languages:
            raise ValueError(f"Unsupported language: {language}")
        
        cfg = self.languages[language]
        compiled_file_id = None
        
        # 1. Compile Phase
        if cfg["compile"]:
            compile_result = self._compile(
                cfg, code, compile_cpu_limit_ns, compile_memory_limit_b
            )
            
            # If compilation failed, return the error for ALL inputs
            if compile_result.get("status") != "Accepted":
                return [compile_result] * len(inputs)
            
            compiled_file_id = compile_result["fileId"]

         # 2. Execution Phase
        try:
            return self._execute_batch(
                cfg, 
                code, 
                compiled_file_id, 
                inputs, 
                exec_cpu_limit_ns, 
                exec_memory_limit_b
            )
        finally:
            # 3. Cleanup
            if compiled_file_id:
                self.cleanup_file(compiled_file_id)
    
    def _compile(self, cfg: dict, code: str, cpu_limit: int, mem_limit: int) -> Dict[str, Any]:
        """Handles the compilation request."""
        logger.info("Compiling...")
        compile_req = {
            "cmd": [{
                "args": cfg["compile"]["args"],
                "env": cfg["compile"]["env"],
                "files": [
                    {"content": ""},
                    {"name": "stdout", "max": 10240},
                    {"name": "stderr", "max": 10240}
                ],
                "cpuLimit": cpu_limit,
                "clockLimit": 2 * cpu_limit,
                "memoryLimit": mem_limit,
                "procLimit": 50,
                "copyIn": {
                    cfg["src_name"]: {"content": code}
                },
                "copyOut": ["stdout", "stderr"],
                "copyOutCached": [cfg["bin_name"]] # Only cache binary
            }]
        }

        try:
            res = requests.post(f"{self.api_url}/run", json=compile_req)
            res.raise_for_status()
            result = res.json()[0]
        except requests.RequestException as e:
            return {"status": "System Error", "stderr": f"Connection failed: {e}"}

        if result["status"] != "Accepted" or result["exitStatus"] != 0:
            return {
                "status": "Compile Error",
                "exit_code": result.get("exitStatus"),
                "stdout": result["files"].get("stdout", ""),
                "stderr": result["files"].get("stderr", ""),
                "metadata": result
            }
        
        # Return success with the file ID
        return {
            "status": "Accepted", 
            "fileId": result["fileIds"][cfg["bin_name"]]
        }

    def _execute_batch(
        self, 
        cfg: dict, 
        code: str, 
        file_id: Optional[str], 
        inputs: List[str], 
        cpu_limit: int, 
        mem_limit: int
    ) -> List[Dict[str, Any]]:
        """
        Executes inputs concurrently using a ThreadPool to send parallel POST requests.
        """
        def _exec_single(index: int, inp: str):
            # Prepare Request
            try:
                copy_in = {}
                if file_id:
                    copy_in[cfg["bin_name"]] = {"fileId": file_id}
                else:
                    copy_in[cfg["src_name"]] = {"content": code}

                run_req = {
                    "cmd": [{
                        "args": cfg["run"]["args"],
                        "env": cfg["run"]["env"],
                        "files": [
                            {"content": inp},
                            {"name": "stdout", "max": 10240},
                            {"name": "stderr", "max": 10240}
                        ],
                        "cpuLimit": cpu_limit,
                        "clockLimit": 2 * cpu_limit,
                        "memoryLimit": mem_limit,
                        "procLimit": 50,
                        "copyIn": copy_in
                    }]
                }

                res = requests.post(f"{self.api_url}/run", json=run_req)
                res.raise_for_status()
                r = res.json()[0]

                # Format Result
                status = r["status"]
                if status == "Accepted" and r["exitStatus"] != 0:
                    status = "Runtime Error"
                
                return index, {
                    "status": status,
                    "exit_code": r.get("exitStatus"),
                    "stdout": r["files"].get("stdout", ""),
                    "stderr": r["files"].get("stderr", ""),
                    "time_ns": r.get("time", 0),
                    "memory_b": r.get("memory", 0)
                }
            except Exception as e:
                logger.error(f"Task {index} failed: {e}")
                return index, {"status": "System Error", "stderr": str(e)}
        
        # Main Parallel Loop
        results = [None] * len(inputs)
        futures = [
            self._executor.submit(_exec_single, i, inp) 
            for i, inp in enumerate(inputs)
        ]
    
        # Collect results as they finish
        for future in as_completed(futures):
            idx, res = future.result()
            results[idx] = res
        
        return results
