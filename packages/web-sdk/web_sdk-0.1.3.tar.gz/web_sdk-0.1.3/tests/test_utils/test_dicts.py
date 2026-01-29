from web_sdk.utils.dicts import merge_dicts


def test_merge_dicts():
    assert merge_dicts(
        {
            "a": 1,
            "b": 2,
        },
        {
            "b": 3,
            "c": 4,
        },
    ) == {
        "a": 1,
        "b": 3,
        "c": 4,
    }
    assert merge_dicts(
        {
            "a": 1,
            "b": 2,
        },
        {
            "b": 3,
            "c": 4,
        },
        {
            "c": 5,
            "d": 6,
        },
    ) == {
        "a": 1,
        "b": 3,
        "c": 5,
        "d": 6,
    }
    assert merge_dicts(
        {
            "a": {
                "a1": 1,
                "a2": {"a21": {"a211": 2, "a212": 3}},
            },
        },
        {
            "a": {
                "a2": {
                    "a21": {
                        "a211": 4,
                        "a213": 5,
                    },
                    "a22": 6,
                },
                "a3": 7,
            },
            "b": {"b1": 8, "b2": 9},
        },
        {"a": {"a4": 10}, "b": {"b2": 11, "b3": 12}, "c": 13},
    ) == {
        "a": {
            "a1": 1,
            "a2": {
                "a21": {
                    "a211": 4,
                    "a212": 3,
                    "a213": 5,
                },
                "a22": 6,
            },
            "a3": 7,
            "a4": 10,
        },
        "b": {
            "b1": 8,
            "b2": 11,
            "b3": 12,
        },
        "c": 13,
    }


def test_merge_dicts_copy():
    dict1 = {"a": []}
    dict2 = {"b": []}

    copy = merge_dicts(dict1, dict2)
    dict1["a"].append(1)
    dict2["b"].append(1)

    assert not len(copy["a"])
    assert not len(copy["b"])

    not_copy = merge_dicts(dict1, dict2, copy=False)
    dict1["a"].append(1)
    dict2["b"].append(1)

    assert len(not_copy["a"]) == len(dict1["a"]) == 2
    assert len(not_copy["b"]) == len(dict2["b"]) == 2
