from meshcomparison.gui import worker
from meshcomparison.gui.config import ProgressTracker, RunConfig, build_commands, validate
from meshcomparison.gui.worker import config_from_json


def _cfg(tmp_path, **kw):
    gt = tmp_path / "gt.stl"
    rm = tmp_path / "rm.stl"
    gt.write_text("x")
    rm.write_text("x")
    return RunConfig(gt=str(gt), rm=str(rm), out=str(tmp_path / "out"), **kw)


def test_validate_accepts_existing_files(tmp_path):
    assert validate(_cfg(tmp_path)) == []


def test_validate_rejects_fbx_and_missing(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.gt = str(tmp_path / "model.fbx")
    cfg.rm = str(tmp_path / "missing.stl")
    errors = validate(cfg)
    assert any("FBX" in e for e in errors)
    assert any("not found" in e for e in errors)


def test_validate_requires_a_pipeline(tmp_path):
    assert validate(_cfg(tmp_path, run_geometry=False, run_perceptual=False))


def test_build_commands_order_and_device(tmp_path):
    python, commands = build_commands(_cfg(tmp_path, device="cuda"), python="py")
    assert python == "py"
    assert [c.name for c in commands] == ["Geometric", "Perceptual"]
    assert all("meshcomparison.gui.worker" in c.args for c in commands)
    assert [c.args[-1] for c in commands] == ["geometry", "perceptual"]
    assert config_from_json(commands[1].stdin).device == "cuda"


def test_run_config_defaults_match_original_pipeline():
    cfg = RunConfig()
    assert (cfg.azimuth, cfg.elevation) == (-135.0, 25.264)
    assert (cfg.width, cfg.height) == (1600, 1200)
    assert cfg.num_views == 100
    assert (cfg.camera_margin, cfg.radius_factor) == (1.05, 1.45)
    assert cfg.mse_threshold == 1e-4


def test_build_commands_pass_default_parameters(tmp_path):
    cfg = _cfg(tmp_path)
    _, commands = build_commands(cfg, python="py")
    for command in commands:
        sent = config_from_json(command.stdin)
        assert sent == cfg
        assert (sent.azimuth, sent.elevation) == (-135.0, 25.264)
        assert (sent.width, sent.height) == (1600, 1200)
        assert (sent.num_views, sent.save_views) == (100, (1, 33, 66))
        assert (sent.camera_margin, sent.radius_factor) == (1.05, 1.45)


def test_config_from_json_ignores_unknown_keys_and_restores_tuples():
    cfg = config_from_json('{"num_views": 9, "save_views": [1, 3], "removed_option": true}')
    assert cfg.num_views == 9 and cfg.save_views == (1, 3)


def test_worker_rejects_unknown_pipeline(capsys):
    assert worker.main(["bogus", "{}"]) == 2
    assert "usage" in capsys.readouterr().err


def test_progress_tracker_follows_custom_view_count():
    t = ProgressTracker(1)
    t.start_command(0)
    t.feed("[6/8] Rendering 9 views and computing metrics...")
    t.feed("    View 003/009 | az=120.00 | LPIPS=0.1")
    assert abs(t.fraction - (5 + 3 / 9) / 8) < 1e-9


def test_progress_tracker_two_commands():
    t = ProgressTracker(2)
    t.start_command(0)
    t.feed("[1/7] Loading meshes...")
    assert t.fraction == 0.0
    t.feed("[5/7] Computing final metrics...")
    assert abs(t.fraction - (4 / 7) / 2) < 1e-9
    t.finish_command()
    assert abs(t.fraction - 0.5) < 1e-9
    t.start_command(1)
    t.feed("[6/8] Rendering 100 views and computing metrics...")
    t.feed("    View 050/100 | az=  1.00 | LPIPS=0.1")
    assert abs(t.fraction - (0.5 + (5.5 / 8) / 2)) < 1e-9
