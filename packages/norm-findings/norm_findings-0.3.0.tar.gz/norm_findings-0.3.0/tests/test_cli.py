import pytest
from norm_findings.stubs.models import Finding, Endpoint, Test

def test_finding_init():
    f = Finding(title="Test Finding", severity="High")
    assert f.title == "Test Finding"
    assert f.severity == "High"
    assert f.unsaved_endpoints == []

def test_endpoint_from_uri():
    e = Endpoint.from_uri("https://example.com/api?q=1")
    assert e.protocol == "https"
    assert e.host == "example.com"
    assert e.path == "/api"
    assert e.query == "q=1"

def test_test_init():
    t = Test(product="MyProduct")
    assert str(t.engagement.product) == "MyProduct"
    assert str(t) == "MyProduct"

def test_cli_import():
    import norm_findings.cli
    assert norm_findings.cli.main is not None

def test_version():
    import norm_findings
    assert hasattr(norm_findings, "__version__")
    assert isinstance(norm_findings.__version__, str)
