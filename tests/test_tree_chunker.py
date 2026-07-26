from app.rag.tree_chunker import TreeChunker

def test_tree_chunker(sample_arabic_text):
    chunker = TreeChunker(parent_size=300, child_size=100)
    tree_res = chunker.build_tree(sample_arabic_text, lesson_id="test_lesson", lesson_title="درس تجريبي")

    parents = tree_res["parents"]
    children = tree_res["children"]

    assert len(parents) > 0
    assert len(children) > 0

    # Test Parent-Child ID relationships
    for child in children:
        assert child.parent_id in parents
        assert child.lesson_id == "test_lesson"
        assert child.level == "child"
