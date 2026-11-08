import pytest

import record


@pytest.mark.parametrize(
    "argv", [["--seconds", "29"], ["--countdown", "-1"], ["--countdown", "two"]]
)
def test_bad_arguments_stop_before_recording(argv, monkeypatch):
    def no_recording(*args, **kwargs):
        """Fails the test if main reaches record()."""
        raise AssertionError("record() ran despite invalid arguments")

    monkeypatch.setattr(record, "record", no_recording)

    with pytest.raises(SystemExit) as exc:
        record.main(argv)
    assert exc.value.code == 2
