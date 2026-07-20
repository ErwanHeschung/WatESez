import io
from pathlib import Path

import pytest

from app.services.noise_remover_service import NoiseRemoverService


class FakeSeparator:
    """Stands in for audio-separator so tests need no model download."""

    def __init__(self, outputs, storage_dir):
        self.outputs = outputs
        self.storage_dir = storage_dir
        self.separated_paths = []

    def separate(self, input_path):
        self.separated_paths.append(input_path)
        written = []
        for name in self.outputs:
            path = self.storage_dir / name
            path.write_bytes(b"STEM:" + name.encode())
            written.append(str(path))
        return written


@pytest.fixture
def service(tmp_path, monkeypatch):
    svc = NoiseRemoverService()
    monkeypatch.setattr(svc, "storage_dir", tmp_path)
    return svc


async def test_returns_the_vocal_stem(service, tmp_path):
    service.separator = FakeSeparator(
        ["song_(Vocals)_model.wav", "song_(Instrumental)_model.wav"], tmp_path
    )

    result = await service.remove_instrumental(b"AUDIO", "song.mp3")

    assert isinstance(result, io.BytesIO)
    assert b"Vocals" in result.getvalue()
    assert result.tell() == 0, "buffer must be rewound for the caller"


async def test_strips_path_traversal_from_the_upload_name(service, tmp_path):
    service.separator = FakeSeparator(["x_(Vocals)_m.wav"], tmp_path)

    await service.remove_instrumental(b"AUDIO", "../../../etc/passwd")

    written = Path(service.separator.separated_paths[0])
    assert written.parent == tmp_path
    assert "passwd" in written.name


async def test_raises_a_useful_error_when_no_vocal_stem_is_produced(service, tmp_path):
    # A bare next() previously raised StopIteration, which says nothing about
    # what actually went wrong if the model's stem naming changes.
    service.separator = FakeSeparator(["song_(Instrumental)_model.wav"], tmp_path)

    with pytest.raises(RuntimeError, match="No vocal stem"):
        await service.remove_instrumental(b"AUDIO", "song.mp3")


async def test_cleans_up_temporary_files_on_success(service, tmp_path):
    service.separator = FakeSeparator(
        ["song_(Vocals)_m.wav", "song_(Instrumental)_m.wav"], tmp_path
    )

    await service.remove_instrumental(b"AUDIO", "song.mp3")

    assert list(tmp_path.iterdir()) == []


async def test_cleans_up_temporary_files_on_failure(service, tmp_path):
    service.separator = FakeSeparator(["song_(Instrumental)_m.wav"], tmp_path)

    with pytest.raises(RuntimeError):
        await service.remove_instrumental(b"AUDIO", "song.mp3")

    assert list(tmp_path.iterdir()) == [], "a failed job must not strand files"
