from pydantic import BaseModel, model_validator, field_validator
from pathlib import Path
from imsi.utils.general import is_root_of

class SetupParams(BaseModel):
    """SetupParams configuration dataclass"""
    runid: str
    model_name: str
    experiment_name: str
    machine_name: str | None
    compiler_name: str | None
    sequencer_name: str | None
    flow_name: str | None
    postproc_profile: str | None
    work_dir: str | Path          # dev: these should really be string
    run_config_path: str | Path   #   because they are rendered as such
    source_repo: str | Path
    fetch_method: str
    source_version: str | None    # None when fetch_method !~ git
    source_path: str | Path
    imsi_config_path: str | Path
    imsi_venv: str

    # TODO construction/validation to be refined/expanded

    @model_validator(mode='after')
    def check_setup_structure(self) -> str:
        for path in [self.run_config_path, self.source_path, self.imsi_config_path]:
            isroot = is_root_of(self.work_dir, path, greedy=False)
            if not isroot:
                raise ValueError(
                    f'setup path {Path(path).name} must be within {self.work_dir}, not at {path}'
                    )
        return self
