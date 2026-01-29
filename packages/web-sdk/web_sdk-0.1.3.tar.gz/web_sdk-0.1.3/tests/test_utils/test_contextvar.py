from web_sdk.utils.contextvar import AtomicContextModes, SimpleContext


def test_simple_context_initialized():
    ctx1 = SimpleContext()
    assert ctx1.initialized is False
    ctx1.__init_context__()
    assert ctx1.initialized is True

    ctx2 = SimpleContext()
    assert ctx2.initialized is False

    ctx2.value
    assert ctx2.initialized is True


def test_simple_context_default():
    default_value = 1

    ctx1 = SimpleContext[int](default=default_value)
    assert ctx1.value == default_value

    default_factory = lambda: default_value

    ctx2 = SimpleContext[int](default_factory=default_factory)
    assert ctx2.value == default_value


def _get_test_simple_context_atomic_data(mode: AtomicContextModes):
    ctx = SimpleContext[dict](default_factory=dict)
    ctx_value = ctx.value

    @ctx.atomic_context
    def depth1() -> tuple[dict, dict, dict]:
        ctx.value["depth1"] = True

        @ctx.atomic_context(mode=mode)
        def depth2() -> tuple[dict, dict]:
            ctx.value["depth2"] = True

            @ctx.atomic_context
            def depth3() -> dict:
                ctx.value["depth3"] = True
                return ctx.value

            return ctx.value, depth3()

        _depth2_ctx, _depth3_ctx = depth2()
        return ctx.value, _depth2_ctx, _depth3_ctx

    depth1_ctx, depth2_ctx, depth3_ctx = depth1()
    return ctx_value, depth1_ctx, depth2_ctx, depth3_ctx


def test_simple_context_atomic_init():
    depth0_ctx, depth1_ctx, depth2_ctx, depth3_ctx = _get_test_simple_context_atomic_data("init")

    assert depth0_ctx == {}
    assert depth1_ctx == {"depth1": True}
    assert depth2_ctx == {"depth2": True}
    assert depth3_ctx == {"depth3": True}


def test_simple_context_atomic_share():
    depth0_ctx, depth1_ctx, depth2_ctx, depth3_ctx = _get_test_simple_context_atomic_data("share")

    assert depth0_ctx == {}
    assert depth1_ctx == {"depth1": True, "depth2": True}
    assert depth2_ctx == {"depth1": True, "depth2": True}
    assert depth3_ctx == {"depth3": True}


def test_simple_context_atomic_copy():
    depth0_ctx, depth1_ctx, depth2_ctx, depth3_ctx = _get_test_simple_context_atomic_data("copy")

    assert depth0_ctx == {}
    assert depth1_ctx == {"depth1": True}
    assert depth2_ctx == {"depth1": True, "depth2": True}
    assert depth3_ctx == {"depth3": True}


def test_simple_context_no_atomic():
    ctx = SimpleContext[dict](default_factory=dict)
    depth0_ctx = ctx.value

    def depth1():
        ctx.value["depth1"] = True

        def depth2():
            ctx.value["depth2"] = True
            return ctx.value

        return ctx.value, depth2()

    depth1_ctx, depth2_ctx = depth1()

    assert depth0_ctx == depth1_ctx == depth2_ctx == {"depth1": True, "depth2": True}
