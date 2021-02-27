import pytest


@pytest.mark.parametrize("url", [
    "http://obviously_a_fake_url/and/some/path",
    "not_an_url_at_all",
    "@&TGJ!KAUYDI@A@Y"
])
def test_register_invalid_url(app_setup, url):
    with app_setup.test_client() as client:
        r = client.post("/devices/register", json={"url": url})
        assert r.status_code == 400


@pytest.mark.parametrize("data", [None, {}, {"url": None}, {"other_param": 12}])
def test_register_no_data(app_setup, data):
    with app_setup.test_client() as client:
        r = client.post("/devices/register", json=data)
        assert r.status_code == 400
