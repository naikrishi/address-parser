from app.services.parse import parse_address


def test_parse_address_complete_components() -> None:
	components, is_complete, confidence = parse_address(
		"3400 W Plano Pkwy, Plano, TX 75075, USA",
		"US",
	)

	assert is_complete is True
	assert confidence == 0.75
	assert components["street_line"] == "3400 W Plano Pkwy"
	assert components["city"] == "Plano"
	assert components["state"] == "TX"
	assert components["postal_code"] == "75075"
	assert components["country"] == "US"


def test_parse_address_incomplete_drops_confidence() -> None:
	components, is_complete, confidence = parse_address("Only Street", None)

	assert is_complete is False
	assert confidence == 0.4
	assert components["street_line"] == "Only Street"
	assert components["city"] is None
	assert components["state"] is None
	assert components["postal_code"] is None


def test_parse_address_whitespace_handling() -> None:
	components, is_complete, confidence = parse_address("  , , TX 75075  ", "")

	assert is_complete is False
	assert confidence == 0.4
	assert components["street_line"] == "TX 75075"
	assert components["city"] is None
	assert components["state"] is None
	assert components["postal_code"] is None
	assert components["country"] is None
