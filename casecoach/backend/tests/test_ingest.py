import pytest

from app.pipelines.ingest import validate_slide_filename, validate_video_filename


def test_video_validation():
    assert validate_video_filename("demo.mp4") == ".mp4"
    with pytest.raises(ValueError):
        validate_video_filename("demo.txt")


def test_slide_validation():
    assert validate_slide_filename("deck.pdf") == ".pdf"
    assert validate_slide_filename("deck.pptx") == ".pptx"
    with pytest.raises(ValueError):
        validate_slide_filename("deck.key")

