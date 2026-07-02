from edu_image_tag.sources.local import LocalFolderSource


def test_local_source_discovers_images_recursively(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.jpg").write_bytes(b"j")
    (tmp_path / "sub" / "b.png").write_bytes(b"p")
    (tmp_path / "notes.txt").write_text("ignore me")

    src = LocalFolderSource(path=str(tmp_path))
    refs = sorted(src.iter_images(), key=lambda r: r.id)

    assert [r.id for r in refs] == ["a.jpg", "sub/b.png"]
    assert refs[0].mime_type == "image/jpeg"
    assert refs[1].mime_type == "image/png"
    assert refs[0].load_bytes() == b"j"


def test_missing_path_raises(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        list(LocalFolderSource(path=str(tmp_path / "nope")).iter_images())
