from epublib.css import CSS


def test_get_urls_basic():
    css = CSS(
        """
        body { background: url(bg.png); }
        .icon { background-image: url("icon.svg"); }
        """
    )

    assert list(css.get_urls()) == ["bg.png", "icon.svg"]


def test_get_urls_variants():
    css = CSS(
        """
        div { background: URL( 'a.png' ); }
        span { background: url(  "b.jpg"  ); }
        """
    )

    assert list(css.get_urls()) == ["a.png", "b.jpg"]


def test_get_urls_multiple_in_same_rule():
    css = CSS(
        """
        body {
            background: url(a.png), url(b.png), url(c.png);
        }
        """
    )

    assert list(css.get_urls()) == ["a.png", "b.png", "c.png"]


def test_replace_urls_simple():
    css = CSS("body { background: url(bg.png); }")

    css.replace_urls(lambda url: f"/static/{url}")

    assert css.content == 'body { background: url("/static/bg.png"); }'


def test_replace_urls_multiple():
    css = CSS(
        """
        .a { background: url(a.png); }
        .b { background: url(b.png); }
        """
    )

    css.replace_urls(lambda url: url.upper())

    assert 'url("A.PNG")' in css.content
    assert 'url("B.PNG")' in css.content


def test_empty_css():
    css = CSS("")

    assert list(css.get_urls()) == []

    css.replace_urls(lambda url: "x")
    assert css.content == ""


def test_replacer_receives_exact_url():
    seen: list[str] = []

    def replacer(url: str):
        seen.append(url)
        return url

    css = CSS("div { background: url( images/bg.png ); }")
    css.replace_urls(replacer)

    assert seen == ["images/bg.png"]


def test_no_urls_present():
    css = CSS("body { color: blue; }")

    css.replace_urls(lambda _: "x")

    assert css.content == "body { color: blue; }"


def test_replace_url_replaces_exact_match():
    css = CSS(
        """
        body { background: url(bg.png); }
        """
    )

    css.replace_url("bg.png", "new.png")

    assert 'url("new.png")' in css.content
    assert "bg.png" not in css.content


def test_replace_url_does_not_replace_other_urls():
    css = CSS(
        """
        body { background: url(bg.png); }
        div  { background: url(other.png); }
        """
    )

    css.replace_url("bg.png", "new.png")

    assert 'url("new.png")' in css.content
    assert "url(other.png)" in css.content


def test_replace_url_multiple_occurrences():
    css = CSS(
        """
        .a { background: url(bg.png); }
        .b { background: url(bg.png); }
        """
    )

    css.replace_url("bg.png", "new.png")

    assert css.content.count('url("new.png")') == 2


def test_replace_url_no_match_no_change():
    original = "body { background: url(bg.png); }"
    css = CSS(original)

    css.replace_url("missing.png", "new.png")

    assert css.content == original


def test_replace_url_preserves_other_content():
    css = CSS(
        """
        body {
            color: red;
            background: url(bg.png);
        }
        """
    )

    css.replace_url("bg.png", "new.png")

    assert "color: red" in css.content
    assert 'url("new.png")' in css.content
