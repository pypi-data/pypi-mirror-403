from immunix.core import Immunix


def test_dummy_failure():
    immune = Immunix()

    @immune.protect
    def always_fail():
        raise ValueError("Fail!")

    result = always_fail()

    # In degraded mode, IMMUNIX must return a structured fallback
    assert isinstance(result, dict)
    assert result["status"] == "DEGRADED"
    assert result["data"] is None
