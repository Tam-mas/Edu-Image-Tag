from edu_image_tag.sources.local import LocalFolderSource
from edu_image_tag.hashing import sha256_hex


def test_local_source_discovers_images_recursively(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.jpg").write_bytes(b"j")
    (tmp_path / "sub" / "b.png").write_bytes(b"p")
    (tmp_path / "notes.txt").write_text("ignore me")

    src = LocalFolderSource(path=str(tmp_path))
    refs = sorted(src.iter_images(), key=lambda r: r.id)

    # ids are "<relpath>#<8-char content hash>"
    assert refs[0].id.startswith("a.jpg#")
    assert refs[1].id.startswith("sub/b.png#")
    assert len(refs[0].id.split("#", 1)[1]) == 8
    assert refs[0].mime_type == "image/jpeg"
    assert refs[1].mime_type == "image/png"
    # load_bytes returns the right file and content_hash matches its content
    assert refs[0].load_bytes() == b"j"
    assert refs[0].content_hash == sha256_hex(b"j")
    assert len(refs[0].content_hash) == 64


def test_missing_path_raises(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        list(LocalFolderSource(path=str(tmp_path / "nope")).iter_images())


def test_identical_bytes_share_hash_but_differ_by_id(tmp_path):
    (tmp_path / "one.jpg").write_bytes(b"SAME")
    (tmp_path / "two.jpg").write_bytes(b"SAME")
    src = LocalFolderSource(path=str(tmp_path))
    refs = sorted(src.iter_images(), key=lambda r: r.id)
    assert refs[0].content_hash == refs[1].content_hash   # identical content
    assert refs[0].id != refs[1].id                        # separate records
