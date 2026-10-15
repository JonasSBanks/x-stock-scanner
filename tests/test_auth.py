from scanner.sources.x_playwright.auth import has_login_cookie


def cookie(name="auth_token", value="abc", domain=".x.com"):
    return {"name": name, "value": value, "domain": domain}


def test_logged_in_cookie_is_detected():
    assert has_login_cookie([cookie(name="guest_id"), cookie()])


def test_old_twitter_domain_also_counts():
    assert has_login_cookie([cookie(domain=".twitter.com")])


def test_no_cookies_means_not_logged_in():
    assert not has_login_cookie([])


def test_other_cookies_alone_mean_not_logged_in():
    assert not has_login_cookie([cookie(name="guest_id"), cookie(name="ct0")])


def test_empty_token_means_not_logged_in():
    assert not has_login_cookie([cookie(value="")])


def test_token_from_another_site_is_ignored():
    assert not has_login_cookie([cookie(domain=".example.com")])
