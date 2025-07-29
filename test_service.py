import pytest
from service import grant_videos, set_premium, decrement_free_generation
from data import add_user, get_user, init_db

def setup_module(module):
    init_db()
    add_user(12345)

def test_grant_videos():
    grant_videos(12345, 2)
    user = get_user(12345)
    assert user.videos_left >= 2

def test_set_premium():
    set_premium(12345, days=1)
    user = get_user(12345)
    assert user.is_premium

def test_decrement_free_generation():
    user = get_user(12345)
    start = user.free_generations
    decrement_free_generation(12345)
    user = get_user(12345)
    assert user.free_generations == max(0, start - 1) 