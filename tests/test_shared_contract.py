from shared.schemas import Symbol, Audit

def test_symbol_schema():
    s = Symbol(id="S001", class_name="pump", tag="P-101A")
    assert s.tag == "P-101A"

def test_audit_schema():
    a = Audit(io_total=1, io_found=1, io_missing=0, io_coverage=100)
    assert a.io_coverage == 100
