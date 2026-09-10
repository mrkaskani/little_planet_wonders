from __future__ import annotations

from types import SimpleNamespace

import torch

from lpw.generation.wan_s2v_backend import DirectWanS2VBackend


def test_initial_noise_is_seed_deterministic() -> None:
    first = DirectWanS2VBackend._initial_noise((1, 2, 3), 42, torch.device("cpu"))
    second = DirectWanS2VBackend._initial_noise((1, 2, 3), 42, torch.device("cpu"))

    assert torch.equal(first, second)


def test_flow_unipc_scheduler_has_20_steps() -> None:
    scheduler = DirectWanS2VBackend._scheduler(20, torch.device("cpu"))

    assert len(scheduler.timesteps) == 20
    assert scheduler.config.prediction_type == "flow_prediction"
    assert scheduler.config.flow_shift == 3.0


def test_scheduler_checkpoint_resumes_unipc_exactly(tmp_path) -> None:
    backend = object.__new__(DirectWanS2VBackend)
    backend.transformer = SimpleNamespace(device=torch.device("cpu"))
    original = backend._scheduler(3, torch.device("cpu"))
    sample = torch.zeros((1, 2, 2), dtype=torch.float32)
    first = original.step(
        torch.ones_like(sample), original.timesteps[0], sample, return_dict=False
    )[0]
    backend._save_scheduler_checkpoint(tmp_path, "matching", original, first, 1, 3)

    restored = backend._scheduler(3, torch.device("cpu"))
    restored_sample, completed = backend._load_scheduler_checkpoint(
        tmp_path, "matching", restored
    )
    prediction = torch.full_like(sample, 0.5)
    expected = original.step(
        prediction, original.timesteps[1], first, return_dict=False
    )[0]
    actual = restored.step(
        prediction, restored.timesteps[1], restored_sample, return_dict=False
    )[0]

    assert completed == 1
    assert restored.step_index == original.step_index
    assert torch.equal(actual, expected)


def test_scheduler_checkpoint_rejects_wrong_signature(tmp_path) -> None:
    backend = object.__new__(DirectWanS2VBackend)
    backend.transformer = SimpleNamespace(device=torch.device("cpu"))
    scheduler = backend._scheduler(2, torch.device("cpu"))
    sample = torch.zeros((1, 2, 2), dtype=torch.float32)
    result = scheduler.step(
        torch.ones_like(sample), scheduler.timesteps[0], sample, return_dict=False
    )[0]
    backend._save_scheduler_checkpoint(tmp_path, "expected", scheduler, result, 1, 2)

    restored = backend._scheduler(2, torch.device("cpu"))
    latents, completed = backend._load_scheduler_checkpoint(
        tmp_path, "different", restored
    )

    assert latents is None
    assert completed == 0
