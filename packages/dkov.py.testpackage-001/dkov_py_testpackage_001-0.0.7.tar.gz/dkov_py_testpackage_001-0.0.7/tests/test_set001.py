import src.utils as src_utils


class TestSet001:
    def test_func1(self):
        assert src_utils.func1() == "Hello World!"
        return

    def test_func2(self):
        assert src_utils.func2() == "It is func2!"
        return

    def test_func3(self):
        assert src_utils.func3() == "It is func3!"
        return
