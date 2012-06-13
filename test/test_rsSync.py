from ..logl import modules


def test_criteria():
    assert logl.modules.rsSync.criteria("some sample log string") == 1
def test_process():
    pass
def test_syncingDiff():
    pass
