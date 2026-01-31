import tomllib
from pathlib import Path
from dataclasses import dataclass
from typing import Self


@dataclass
class DDDifyConfig:
    output_dir: str = "."
    
    @classmethod
    def load(cls, config_path: Path | None = None) -> Self:
        if config_path is None:
            for filename in ["dddify.toml", "pyproject.toml"]:
                candidate = Path.cwd() / filename
                if candidate.exists():
                    config_path = candidate
                    break
        
        if config_path is None or not config_path.exists():
            return cls()
        
        print("Lade Konfiguration von:", config_path)
        
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        
        # Support both: dddify.toml with [dddify] and pyproject.toml with [tool.dddify]
        if "tool" in data and "dddify" in data["tool"]:
            config = data["tool"]["dddify"]
        elif "dddify" in data:
            config = data["dddify"]
        else:
            return cls()
        
        return cls(
            output_dir=config.get("output_dir", ".")
        )