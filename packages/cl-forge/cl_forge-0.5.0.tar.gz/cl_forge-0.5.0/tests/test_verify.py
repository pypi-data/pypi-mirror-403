import pytest

from cl_forge import exceptions, verify


def test_validate_rut_valid():
    assert verify.validate_rut("12345678", "5") is True
    assert verify.validate_rut("11222333", "9") is True
    assert verify.validate_rut("9000000", "4") is True
    assert verify.validate_rut("1", "9") is True

def test_validate_rut_invalid():
    assert verify.validate_rut("12345678", "0") is False
    assert verify.validate_rut("12345678", "K") is False

def test_calculate_verifier():
    assert verify.calculate_verifier("12345678") == "5"
    assert verify.calculate_verifier("11222333") == "9"
    assert verify.calculate_verifier("9000000") == "4"
    assert verify.calculate_verifier("1") == "9"
    assert verify.calculate_verifier("18305086") == "9"
    assert verify.calculate_verifier("14682029") == "8"

def test_ppu_class():
    ppu = verify.Ppu("PHZF55")
    assert ppu.normalized == "PHZF55"
    assert ppu.verifier == "K"
    assert ppu.complete == "PHZF55-K"
    assert ppu.numeric == "069455"

def test_ppu_class_3_2():
    # LLLNN -> LLL0NN
    ppu = verify.Ppu("BBC12")
    assert ppu.normalized == "BBC012"
    assert ppu.format == "LLLNN"

def test_normalize_ppu():
    assert verify.normalize_ppu("bbc12") == "BBC012"
    assert verify.normalize_ppu("bbcd12") == "BBCD12"


def test_generate_success():
    n = 10
    min_val = 1_000_000
    max_val = 2_000_000
    results = verify.generate(n, min_val, max_val)
    
    assert len(results) == n
    correlatives = set()
    for item in results:
        correlative = item['correlative']
        verifier = item['verifier']
        assert min_val <= correlative < max_val # type: ignore
        assert verify.validate_rut(str(correlative), verifier) is True # type: ignore
        correlatives.add(correlative)
    
    assert len(correlatives) == n

def test_generate_seed():
    n = 5
    min_val = 1_000_000
    max_val = 2_000_000
    seed = 12345
    
    results1 = verify.generate(n, min_val, max_val, seed=seed)
    results2 = verify.generate(n, min_val, max_val, seed=seed)
    
    assert results1 == results2

def test_generate_invalid_input():
    # n <= 0
    with pytest.raises(exceptions.InvalidInput):
        verify.generate(0, 1000, 2000)
    
    # min < 0
    with pytest.raises(exceptions.InvalidInput):
        verify.generate(10, -1, 2000)
    
    # max < 0
    with pytest.raises(exceptions.InvalidInput):
        verify.generate(10, 1000, -1)
        
    # seed < 0
    with pytest.raises(exceptions.InvalidInput):
        verify.generate(10, 1000, 2000, seed=-5)

def test_generate_invalid_range():
    # min >= max
    with pytest.raises(exceptions.InvalidRange):
        verify.generate(10, 2000, 1000)
    
    with pytest.raises(exceptions.InvalidRange):
        verify.generate(10, 1000, 1000)

def test_generate_insufficient_range():
    # n > (max - min + 1)
    with pytest.raises(exceptions.InsufficientRange):
        verify.generate(12, 1000, 1010)
