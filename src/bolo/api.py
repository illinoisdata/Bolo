import os
import re
import ast
import json
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path
from jinja2 import Environment, StrictUndefined

from ._version import __version__, __templates_version__

_TEMPLATES_RELEASE_URL = (
    "https://github.com/illinoisdata/bolo-templates/releases/download/"
    "v{version}/templates.tar.gz"
)


class InferClient:
    _instance = None
    _torch_cu128_url = "https://download.pytorch.org/whl/cu128"

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.db_dir = self._ensure_templates()
        self.supported_models = set()

        for rid_dir in self.db_dir.iterdir():
            if rid_dir.is_dir():
                repo_name = rid_dir.name
                repo_id = "/".join(repo_name.split('__SEP__'))
                self.supported_models.add(repo_id)

        self._initialized = True

    @staticmethod
    def _ensure_templates() -> Path:
        env_path = os.environ.get("BOLO_TEMPLATES_DIR")
        if env_path:
            return Path(env_path).expanduser()

        local = Path(__file__).parent / "templates"
        if local.exists() and any(local.iterdir()):
            return local

        cache_root = Path.home() / ".cache" / "bolo" / "templates"
        cache = cache_root / __templates_version__
        if cache.exists() and any(cache.iterdir()):
            return cache

        url = _TEMPLATES_RELEASE_URL.format(version=__templates_version__)
        print(f"fetching bolo templates v{__templates_version__} from {url} ...", flush=True)

        cache_root.mkdir(parents=True, exist_ok=True)
        tmp = cache_root / f".tmp.{__templates_version__}"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir()

        try:
            with urllib.request.urlopen(url) as resp, tarfile.open(fileobj=resp, mode="r|gz") as tar:
                tar.extractall(tmp)
            tmp.rename(cache)
        except Exception:
            shutil.rmtree(tmp, ignore_errors=True)
            raise

        return cache

    @staticmethod
    def _bolo_install_args() -> list[str]:
        """Args to pass to `uv pip install` when seeding bolo into a model venv."""
        project_root = Path(__file__).resolve().parent.parent.parent
        if (project_root / "pyproject.toml").exists():
            return ["-e", str(project_root)]
        return ["bolo"]
            
    def query_a_repo(self, repo_id: str):
        if repo_id not in self.supported_models:
            print(f"bolo does not support {repo_id}")
            return False
        
        return True
    
    def create_venv(self, repo_id: str, venv_path: str | Path | None = None):
        repo_name = "__SEP__".join(repo_id.split('/'))
        
        if not venv_path:
            venv_path = self.db_dir / "tmp_venv" / repo_name
            print(f"you do not specify the venv path for {repo_id}, we create by default at {venv_path}")
        
        if venv_path.exists():
            print(f"ven for {repo_id} has been already existed")
            return venv_path / "bin" / "python", True
        
        os.makedirs(venv_path, exist_ok=True)
        
        req_txt = self.db_dir / repo_name / "requirements.txt"
        
        cmd1 = ['uv', 'venv', str(venv_path), '--python', '3.13']
        try:
            subprocess.run(cmd1, check=True, text=True, capture_output=True)
        except Exception as e:
            print(f"failed to create uv venv for {repo_id}, due to the following error : ")
            print(e.stderr)
            return "", False
        
        python_bin = venv_path / "bin" / "python"
        cmd2 = ['uv', 'pip', 'install', '-r', str(req_txt), '--python', str(python_bin), '--extra-index-url', self._torch_cu128_url]
        try:
            subprocess.run(cmd2, check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"failed to install requirements.txt for {repo_id}, due to the following error : ")
            print(e.stderr)
            return "", False

        cmd3 = ['uv', 'pip', 'install', *self._bolo_install_args(), '--python', str(python_bin)]
        try:
            subprocess.run(cmd3, check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"failed to install bolo into the venv for {repo_id}, due to the following error : ")
            print(e.stderr)
            return "", False

        print(f"installed requirements.txt and bolo in a venv : {python_bin}!")
        return python_bin, True
    
    def remove_venv(self, repo_id: str, venv_path: str | Path | None = None):
        repo_name = "__SEP__".join(repo_id.split('/'))
        if not venv_path:
            venv_path = self.db_dir / "tmp_venv" / repo_name
        shutil.rmtree(venv_path, ignore_errors=True)
            
    def render_template(self, repo_id: str, params: dict):
        rid_name = "__SEP__".join(repo_id.split('/'))
        template_path = self.db_dir / rid_name / "template.j2"
        
        params["repo_id"] = repo_id
        
        with open(template_path, 'r', encoding="utf-8") as f:
            template = f.read().strip()
            
        try:
            rendered_script = Environment(undefined=StrictUndefined).from_string(template).render(**params)
        except Exception as e:
            print(f"failed to render template for {repo_id}m due to the following error : ")
            print(e)
            return "", False
        
        return rendered_script, True
    
    def list_params(self, repo_id: str):
        rid_name = "__SEP__".join(repo_id.split('/'))
        template_path = self.db_dir / rid_name / "template.j2"
        
        with open(template_path, 'r', encoding="utf-8") as f:
            template = f.read().strip()
        
        set_pattern = re.compile(r'^\s*\{\%\s*set\s+([a-zA-Z_]\w*)\s*=\s*(.*?)\s*\%\}\s*$')
        lines = template.splitlines()
        params = []
        started = False
        
        for line in lines:
            matched = set_pattern.match(line)
            if matched:
                started = True
                name = matched.group(1)
                raw_default = matched.group(2).strip()
                
                lowered = raw_default.lower()
                if lowered == "true":
                    default = True
                elif lowered == "false":
                    default = False
                elif lowered in {"none", "null"}:
                    default = None
                else:
                    try:
                        default = ast.literal_eval(raw_default)
                    except Exception:
                        default = raw_default
                
                if name == "repo_id" or name == "output_dir":
                    continue
                
                params.append(
                    {
                        "name": name,
                        "default": default,
                        "type": type(default).__name__,
                        "raw_default": raw_default,
                    }
                )
                continue
            
            if started:
                break
        
        if not any(p["name"] == "device" for p in params):
            params.insert(0, {
                "name": "device",
                "default": "<required>",
                "type": "str",
                "raw_default": "<required>",
            })

        result = {
            "num_params": len(params),
            "params": params,
        }

        def _to_display(v):
            if isinstance(v, (dict, list)):
                return json.dumps(v, ensure_ascii=False)
            return str(v)

        headers = ["name", "type", "default", "raw_default"]
        rows = [
            [p["name"], p["type"], p["default"], p["raw_default"]]
            for p in params
        ]
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(_to_display(cell)))

        print(f"repo_id: {_to_display(repo_id)}")
        print(f"num_params: {_to_display(len(params))}")
        if not rows:
            print("(no top-level Jinja set variables found)")
            return result
        
        sep = " | "
        header_line = sep.join(headers[i].ljust(widths[i]) for i in range(len(headers)))
        divider = "-+-".join("-" * widths[i] for i in range(len(headers)))
        print(header_line)
        print(divider)
        for row in rows:
            print(sep.join(_to_display(row[i]).ljust(widths[i]) for i in range(len(headers))))
        
        return result
    
    def run_inference(self, code: str):
        try:
            ns = {"__name__": "__api__"}
            exec(code, ns, ns)
            if "RESULT" not in ns:
                raise RuntimeError("RESULT not defined")
            return ns["RESULT"]
        except Exception:
            raise
        
        
def list_params(repo_id: str):
    client = InferClient()
    
    is_exist = client.query_a_repo(repo_id)
    if not is_exist:
        raise ValueError(f"bolo does not support {repo_id}")
    
    _ = client.list_params(repo_id)
        
        
def create_a_venv(repo_id: str, venv_path: str | Path | None = None):
    client = InferClient()
    
    is_exist = client.query_a_repo(repo_id)
    if not is_exist:
        raise ValueError(f"bolo does not support {repo_id}")
    
    if venv_path is not None and os.path.exists(venv_path):
        print(f"already created venv at : {venv_path}")
        return venv_path
    
    venv_path, staus = client.create_venv(repo_id, venv_path)
    
    if not staus:
        raise RuntimeError(f"failed to create venv for {repo_id}")
    
    return venv_path
    
    
def pipeline(repo_id: str, **kwargs):
    client = InferClient()
    
    is_exist = client.query_a_repo(repo_id)
    if not is_exist:
        raise ValueError(f"bolo does not support {repo_id}")
    
    _ = client.list_params(repo_id)
    
    code, is_success = client.render_template(repo_id, kwargs)
    if not is_success:
        raise RuntimeError(f"failed to render template for {repo_id}")

    return client.run_inference(code)
    
    
def remove_venv(repo_id: str):
    client = InferClient()
    client.remove_venv(repo_id)


def fetch_templates() -> Path:
    """Pre-populate the bolo templates cache (downloads from the GitHub release if needed)."""
    path = InferClient._ensure_templates()
    print(f"templates available at : {path}")
    return path