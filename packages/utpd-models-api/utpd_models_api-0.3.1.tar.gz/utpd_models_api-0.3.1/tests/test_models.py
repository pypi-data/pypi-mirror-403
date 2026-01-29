"""Test that models can parse real API responses."""

from pathlib import Path

import pytest
from utpd_models_api import CheckinRecent, UserBeers, UserCheckins, UserFriends, UserInfo

SAMPLES = Path(__file__).parent / "samples"

MODELS = [
    ("checkin_recent.json", CheckinRecent),
    ("user_checkins.json", UserCheckins),
    ("user_beers.json", UserBeers),
    ("user_friends.json", UserFriends),
    ("user_info.json", UserInfo),
]


@pytest.mark.parametrize(
    "filename,model", MODELS, ids=[m[0].replace(".json", "") for m in MODELS]
)
def test_parse_sample(filename: str, model: type) -> None:
    """Parse each sample with its corresponding model."""
    sample = SAMPLES / filename
    if not sample.exists():  # pragma: no cover
        pytest.skip(f"Sample {filename} not found - add API sample to tests/samples/")

    data = sample.read_text()
    result = model.model_validate_json(data)
    assert result.meta.code == 200


def test_samples_exist() -> None:
    """Ensure at least one sample exists for meaningful test coverage."""
    existing = [f for f, _ in MODELS if (SAMPLES / f).exists()]
    if not existing:  # pragma: no cover
        pytest.skip("No samples found yet - add API samples to tests/samples/")


# === Nested model validation tests ===
# These verify that models are properly populated, not just passing via Any


class TestCheckinRecent:
    """Validate nested models in checkin_recent response."""

    @pytest.fixture
    def data(self) -> CheckinRecent:
        sample = SAMPLES / "checkin_recent.json"
        if not sample.exists():  # pragma: no cover
            pytest.skip("checkin_recent.json not found")
        return CheckinRecent.model_validate_json(sample.read_text())

    def test_has_checkins(self, data: CheckinRecent) -> None:
        assert data.response.checkins.count > 0
        assert len(data.response.checkins.items) > 0

    def test_checkin_has_beer(self, data: CheckinRecent) -> None:
        checkin = data.response.checkins.items[0]
        assert checkin.beer.bid > 0
        assert checkin.beer.beer_name.strip() != ""
        assert checkin.beer.beer_style.strip() != ""

    def test_checkin_has_brewery(self, data: CheckinRecent) -> None:
        checkin = data.response.checkins.items[0]
        assert checkin.brewery.brewery_id > 0
        assert checkin.brewery.brewery_name.strip() != ""
        assert checkin.brewery.country_name.strip() != ""

    def test_checkin_has_user(self, data: CheckinRecent) -> None:
        checkin = data.response.checkins.items[0]
        assert checkin.user.uid > 0
        assert checkin.user.user_name.strip() != ""


class TestUserCheckins:
    """Validate nested models in user_checkins response."""

    @pytest.fixture
    def data(self) -> UserCheckins:
        sample = SAMPLES / "user_checkins.json"
        if not sample.exists():  # pragma: no cover
            pytest.skip("user_checkins.json not found")
        return UserCheckins.model_validate_json(sample.read_text())

    def test_has_checkins(self, data: UserCheckins) -> None:
        assert data.response.checkins.count > 0
        assert len(data.response.checkins.items) > 0

    def test_checkin_has_beer(self, data: UserCheckins) -> None:
        checkin = data.response.checkins.items[0]
        assert checkin.beer.bid > 0
        assert checkin.beer.beer_name.strip() != ""

    def test_checkin_has_brewery(self, data: UserCheckins) -> None:
        checkin = data.response.checkins.items[0]
        assert checkin.brewery.brewery_id > 0
        assert checkin.brewery.brewery_name.strip() != ""


class TestUserBeers:
    """Validate nested models in user_beers response."""

    @pytest.fixture
    def data(self) -> UserBeers:
        sample = SAMPLES / "user_beers.json"
        if not sample.exists():  # pragma: no cover
            pytest.skip("user_beers.json not found")
        return UserBeers.model_validate_json(sample.read_text())

    def test_has_beers(self, data: UserBeers) -> None:
        assert data.response.beers.count > 0
        assert len(data.response.beers.items) > 0

    def test_beer_item_has_beer(self, data: UserBeers) -> None:
        item = data.response.beers.items[0]
        assert item.beer.bid > 0
        assert item.beer.beer_name.strip() != ""
        assert item.count > 0

    def test_beer_item_has_brewery(self, data: UserBeers) -> None:
        item = data.response.beers.items[0]
        assert item.brewery.brewery_id > 0
        assert item.brewery.brewery_name.strip() != ""

    def test_user_beer_ordering_and_hashing(self, data: UserBeers) -> None:
        """Test that UserBeer supports comparison and hashing for use in sets/sorting."""
        items = data.response.beers.items
        if len(items) < 2:  # pragma: no cover
            pytest.skip("Need at least 2 beers to test ordering")

        beer1 = items[0].beer
        beer2 = items[1].beer

        # Test equality
        same_beer = beer1
        assert beer1 == same_beer
        assert (beer1 == beer2) == (beer1.bid == beer2.bid)

        # Test ordering
        assert (beer1 < beer2) == (beer1.bid < beer2.bid)

        # Test hashing (can be used in sets)
        beer_set = {beer1, beer2}
        assert len(beer_set) == (1 if beer1.bid == beer2.bid else 2)

        # Test comparison with non-UserBeer returns NotImplemented
        assert beer1.__eq__("not a beer") is NotImplemented
        assert beer1.__lt__("not a beer") is NotImplemented


class TestUserFriends:
    """Validate nested models in user_friends response."""

    @pytest.fixture
    def data(self) -> UserFriends:
        sample = SAMPLES / "user_friends.json"
        if not sample.exists():  # pragma: no cover
            pytest.skip("user_friends.json not found")
        return UserFriends.model_validate_json(sample.read_text())

    def test_has_friends(self, data: UserFriends) -> None:
        assert data.response.count > 0
        assert len(data.response.items) > 0

    def test_friend_has_user(self, data: UserFriends) -> None:
        friend = data.response.items[0]
        assert friend.user.uid > 0
        assert friend.user.user_name.strip() != ""
        assert friend.friendship_hash.strip() != ""


class TestUserInfo:
    """Validate nested models in user_info response."""

    @pytest.fixture
    def data(self) -> UserInfo:
        sample = SAMPLES / "user_info.json"
        if not sample.exists():  # pragma: no cover
            pytest.skip("user_info.json not found")
        return UserInfo.model_validate_json(sample.read_text())

    def test_has_user(self, data: UserInfo) -> None:
        assert data.response.user.uid > 0
        assert data.response.user.user_name.strip() != ""

    def test_user_has_stats(self, data: UserInfo) -> None:
        stats = data.response.user.stats
        assert stats.total_checkins >= 0
        assert stats.total_beers >= 0
        assert stats.total_badges >= 0
