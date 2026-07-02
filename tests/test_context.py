from edu_image_tag.context import load_context_lookup


def test_no_context_file_returns_empty_lookup():
    lookup = load_context_lookup(None)
    assert lookup.get("anything").fields == {}


def test_csv_context_maps_by_id(tmp_path):
    p = tmp_path / "ctx.csv"
    p.write_text("image_id,textbook_title,chapter\n"
                 "a/b.jpg,Biology,4\n")
    lookup = load_context_lookup(str(p))
    ctx = lookup.get("a/b.jpg")
    assert ctx.fields["textbook_title"] == "Biology"
    assert ctx.fields["chapter"] == "4"
    assert lookup.get("missing.jpg").fields == {}


def test_json_context_maps_by_id(tmp_path):
    p = tmp_path / "ctx.json"
    p.write_text('{"a/b.jpg": {"textbook_title": "Bio", "chapter": "4"}}')
    lookup = load_context_lookup(str(p))
    assert lookup.get("a/b.jpg").fields["textbook_title"] == "Bio"
