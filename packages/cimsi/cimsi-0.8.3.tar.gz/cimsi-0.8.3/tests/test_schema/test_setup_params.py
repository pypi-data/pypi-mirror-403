import pytest
from pydantic import ValidationError
from imsi.config_manager.schema.setup_params import SetupParams

# TODO this is currently a stub, to be refined and expanded

@pytest.fixture
def valid_setup_params_data():
    """Fixture to provide valid setup param data."""
    return {
        'runid': 'abc-123',
        'model_name': 'test_model',
        'experiment_name': 'test_exp',
        'machine_name': 'test_machine',
        'compiler_name': 'test_compiler',
        'sequencer_name': 'test_seq',
        'flow_name': 'test_flow',
        'postproc_profile': 'test_postproc',
        'work_dir': '/path/to/work_dir',
        'run_config_path': '/path/to/work_dir/config',
        'source_repo': '/path/to/work_dir/source_repo',
        'fetch_method': 'copy',
        'source_version': None,
        'source_path': '/path/to/work_dir/src',
        'imsi_config_path': '/path/to/work_dir/src/imsi-config',
        'imsi_venv': 'imsi_venv_path'
    }


def test_init(valid_setup_params_data):
    SetupParams(**valid_setup_params_data)


def test_required_fields(valid_setup_params_data):
    """Ensure some fields can be None."""
    valid_setup_params_data['machine_name'] = None
    valid_setup_params_data['compiler_name'] = None
    valid_setup_params_data['sequencer_name'] = None
    valid_setup_params_data['flow_name'] = None

    sp = SetupParams(**valid_setup_params_data)

    assert sp.machine_name is None
    assert sp.compiler_name is None
    assert sp.sequencer_name is None
    assert sp.flow_name is None


def test_invalid_path_setup(valid_setup_params_data):
    valid_setup_params_data['source_path'] = '/fake/path/imsi-config'
    with pytest.raises(ValidationError):
        SetupParams(**valid_setup_params_data)
