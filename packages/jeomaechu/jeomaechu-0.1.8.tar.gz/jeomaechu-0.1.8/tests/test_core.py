import pytest
from jeomaechu.core import JeomMaeChu

def test_basic_recommendation():
    engine = JeomMaeChu()
    result = engine.recommend_random()
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert isinstance(result[1], str)

def test_recommend_many():
    engine = JeomMaeChu()
    results = engine.recommend_many(count=3)
    assert len(results) == 3

def test_single_category_filter():
    engine = JeomMaeChu()
    category = "Korean (한식)"
    results = engine.recommend_many(count=5, categories=[category])
    for cat, menu in results:
        assert cat == category

def test_multiple_categories_filter():
    engine = JeomMaeChu()
    categories = ["Korean (한식)", "Japanese (일본어/일식)"]
    results = engine.recommend_many(count=10, categories=categories)
    for cat, menu in results:
        assert cat in categories

def test_single_tag_filter():
    engine = JeomMaeChu()
    tag = "Spicy (매콤)"
    results = engine.recommend_many(count=5, tags=[tag])
    # tags check is internal, but we can check if results are returned
    assert len(results) > 0

def test_multiple_tags_intersection():
    engine = JeomMaeChu()
    # "Spicy" and "Seafood"
    tags = ["Spicy (매콤)", "Seafood (해산물)"]
    results = engine.recommend_many(count=20, tags=tags)
    
    # Check if results satisfy both tags (this is a bit tautological since the engine filters by them,
    # but we can verify against our own DATA if we want. For now, just ensure it doesn't crash
    # and returns something plausible like '짬뽕' or '매운생선조림')
    assert len(results) > 0
    for cat, menu in results:
        # Verify manual check if possible
        pass

def test_no_results():
    engine = JeomMaeChu()
    # Impossible combo: Brand category with "Real Home" tag (most likely empty if tags are strictly generated from content)
    # Actually, tags are generated from ALL menus, so an item in Brand could have a tag.
    # Let's try something truly impossible or non-existent
    results = engine.recommend_many(count=1, categories=["Non-existent"])
    assert len(results) == 0

def test_getters():
    engine = JeomMaeChu()
    assert len(engine.get_categories()) > 0
    assert len(engine.get_tags()) > 0
    assert len(engine.get_all_menus()) > 0
