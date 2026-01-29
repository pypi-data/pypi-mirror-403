from immunix.core import Immunix

def test_dummy_success():
    immune = Immunix()
    
    @immune.protect
    def always_succeed():
        return 42
    
    assert always_succeed() == 42
