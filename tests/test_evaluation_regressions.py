from types import SimpleNamespace
from unittest.mock import patch

from src.ml.config import YoloExperimentConfig
from src.ml.training import evaluate_model


def test_evaluation_uses_test_split_and_actual_run_directory(tmp_path):
    weights = tmp_path / 'fixture.pt'
    weights.write_bytes(b'unit-test fixture')
    actual_run = tmp_path / 'evaluation2'
    config = YoloExperimentConfig(project=str(tmp_path))
    dataset = SimpleNamespace(dataset_yaml=tmp_path / 'dataset.yaml', split_counts={'test': 1})
    arguments = {}

    def evaluate(**kwargs):
        arguments.update(kwargs)
        return SimpleNamespace(save_dir=actual_run, results_dict={})

    with patch('src.ml.training.validate_yolo_dataset', return_value=dataset) as validate:
        result = evaluate_model(weights, config, model_factory=lambda _: SimpleNamespace(val=evaluate))
    assert validate.call_args.kwargs['require_test'] is True
    assert arguments['split'] == 'test'
    assert result['dataset']['evaluated_split'] == 'test'
    assert (actual_run / 'metrics.json').is_file()
