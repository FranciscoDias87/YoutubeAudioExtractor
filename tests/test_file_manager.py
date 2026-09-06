import os

from file_manager import FileManager


def test_create_temp_directory_is_inside_base_directory(tmp_path):
    manager = FileManager(str(tmp_path))
    temp_dir = manager.create_temp_directory()

    assert os.path.isdir(temp_dir)
    assert os.path.dirname(temp_dir) == str(tmp_path)
    manager.cleanup_directory(temp_dir)
    assert not os.path.exists(temp_dir)


def test_list_files_is_scoped_to_requested_directory(tmp_path):
    manager = FileManager(str(tmp_path))
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    (isolated / "track.mp3").write_bytes(b"audio")
    (isolated / "notes.txt").write_text("ignore", encoding="utf-8")
    (tmp_path / "outside.mp3").write_bytes(b"outside")

    files = manager.list_files(str(isolated), {".mp3"})

    assert files == [str(isolated / "track.mp3")]


def test_get_unique_path_never_overwrites_existing_file(tmp_path):
    manager = FileManager(str(tmp_path))
    first = tmp_path / "Artist - Song.mp3"
    first.write_bytes(b"existing")

    unique = manager.get_unique_path(str(tmp_path), first.name)

    assert unique == str(tmp_path / "Artist - Song (1).mp3")
    assert first.read_bytes() == b"existing"


def test_move_file_uses_unique_destination(tmp_path):
    manager = FileManager(str(tmp_path))
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    destination_dir = tmp_path / "destination"
    destination_dir.mkdir()
    existing = destination_dir / "song.mp3"
    existing.write_bytes(b"old")
    source = source_dir / "song.mp3"
    source.write_bytes(b"new")

    moved = manager.move_file(str(source), str(destination_dir))

    assert moved == str(destination_dir / "song (1).mp3")
    assert not source.exists()
    assert (destination_dir / "song (1).mp3").read_bytes() == b"new"
    assert existing.read_bytes() == b"old"


def test_get_unique_output_path_respects_audio_format(tmp_path):
    manager = FileManager(str(tmp_path))

    output = manager.get_unique_output_path("Artist - Song", "mp3")

    assert output == str(tmp_path / "Artist - Song.mp3")


def test_sanitize_filename_removes_trailing_dot_and_invalid_characters(tmp_path):
    manager = FileManager(str(tmp_path))

    sanitized = manager.sanitize_filename('Song: test?*.')

    assert sanitized == "Song test"
