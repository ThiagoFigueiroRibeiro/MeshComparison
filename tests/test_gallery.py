from meshcomparison.gui.gallery import collect_image_entries


def _touch(root, *parts):
    path = root.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return str(path)


def test_entries_pair_gt_and_rm_from_the_same_view(tmp_path):
    _touch(tmp_path, "renders", "gt_ortho.png")
    _touch(tmp_path, "renders", "rm_aligned_ortho.png")
    _touch(tmp_path, "heatmaps", "gt_heatmap_ortho.png")
    for n in ("001", "033"):
        _touch(tmp_path, "renders", "gt", f"gt_view{n}.png")
        _touch(tmp_path, "renders", "rm", f"rm_view{n}.png")
    _touch(tmp_path, "renders", "pairs", "pair_view001.png")  # already a composite: not used

    entries = collect_image_entries(str(tmp_path))

    assert [title for title, _ in entries] == [
        "Geometric view", "Deviation heatmap", "Perceptual view 001", "Perceptual view 033"]
    assert [[caption for caption, _ in images] for _, images in entries] == [
        ["GT", "RM aligned"], ["GT vertex distance to aligned RM"], ["GT", "RM aligned"], ["GT", "RM aligned"]]


def test_entries_sort_views_numerically_and_handle_missing_rm(tmp_path):
    for n in ("100", "009"):
        _touch(tmp_path, "renders", "gt", f"gt_view{n}.png")
    _touch(tmp_path, "renders", "rm", "rm_view009.png")

    entries = collect_image_entries(str(tmp_path))

    assert [title for title, _ in entries] == ["Perceptual view 009", "Perceptual view 100"]
    assert len(entries[0][1]) == 2 and len(entries[1][1]) == 1


def test_entries_empty_for_empty_output(tmp_path):
    assert collect_image_entries(str(tmp_path)) == []
