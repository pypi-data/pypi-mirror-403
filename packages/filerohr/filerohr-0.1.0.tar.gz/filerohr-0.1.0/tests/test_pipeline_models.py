from filerohr.pipeline.models import AudioMetadata


def test_merge_two_audio_metadata_without_overwrite():
    meta_1 = AudioMetadata(artist="artist 1")
    meta_2 = AudioMetadata(artist="artist 2", title="title 2")
    merged = meta_1.merge(meta_2)
    assert merged is not meta_1
    assert merged is not meta_2
    assert merged.artist == "artist 1"
    assert merged.title == "title 2"


def test_merge_two_audio_metadata_with_overwrite():
    meta_1 = AudioMetadata(artist="artist 1", album="album 1")
    meta_2 = AudioMetadata(artist="artist 2", title="title 2")
    merged = meta_1.merge(meta_2, overwrite=True)
    assert merged is not meta_1
    assert merged is not meta_2
    assert merged.artist == "artist 2"
    assert merged.title == "title 2"
    assert merged.album == "album 1"
