from web_sdk.utils.url import join_path


def test_join_path_full_cases():
    assert join_path("") == ""
    assert join_path("/foo") == "/foo"
    assert join_path("foo/") == "foo/"
    assert join_path("", None) == ""  # type: ignore
    assert join_path("/", None) == "/"  # type: ignore
    assert join_path("foo/", None) == "foo/"  # type: ignore
    assert join_path("/foo", None) == "/foo"  # type: ignore
    assert join_path("", None, "") == ""  # type: ignore
    assert join_path("/", None, "/") == "/"  # type: ignore
    assert join_path("foo/", None, "bar/") == "foo/bar/"  # type: ignore
    assert join_path("/foo", None, "bar") == "/foo/bar"  # type: ignore
    assert join_path("{arg1}", None, "{arg2}", arg1=1, arg2="2") == "1/2"  # type: ignore

    assert join_path(
        "https://example.com/",
        "/with_prefix_and_suffix/",
        "without_prefix/",
        "/without_suffix",
        "without_suffix_and_prefix",
        "with/slash/in/part",
        None,  # type: ignore
        "",
        "with_{parameter}_in/",
        parameter="value",
    ) == (
        "https://example.com/"
        "with_prefix_and_suffix/"
        "without_prefix/"
        "without_suffix/"
        "without_suffix_and_prefix/"
        "with/"
        "slash/"
        "in/"
        "part/"
        "with_value_in/"
    )
