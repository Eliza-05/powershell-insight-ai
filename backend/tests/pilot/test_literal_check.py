from app.services.evidence.literal_check import EvidenceLocation, is_verifiable, locate

SCRIPT = "$c = 'Invoke-' + 'WebRequest'\n& $c -Uri $u"
REFS = {"base": "Invoke-WebRequest -Uri 'https://example.com/report.csv'"}


def test_exact_in_input():
    assert locate("& $c -Uri $u", SCRIPT, REFS)[0] is EvidenceLocation.INPUT_EXACT


def test_surrounding_whitespace_is_ignored():
    assert locate("  & $c -Uri $u\n", SCRIPT, REFS)[0] is EvidenceLocation.INPUT_EXACT


def test_found_only_in_reference():
    assert locate("Invoke-WebRequest", SCRIPT, REFS) == (EvidenceLocation.REFERENCE_EXACT, "base")


def test_normalized_match_is_not_verifiable():
    location, _ = locate("& $C   -uri $U", SCRIPT, REFS)
    assert location is EvidenceLocation.NORMALIZED_ONLY
    assert not is_verifiable(location)


def test_invented_and_empty_snippets():
    assert locate("Start-BitsTransfer", SCRIPT, REFS)[0] is EvidenceLocation.NOT_FOUND
    assert locate("   ", SCRIPT, REFS)[0] is EvidenceLocation.EMPTY
