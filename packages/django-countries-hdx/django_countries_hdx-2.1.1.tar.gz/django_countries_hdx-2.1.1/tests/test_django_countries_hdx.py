from unittest import TestCase
from django_countries_hdx import (
    countries_by_region,
    countries_by_subregion,
    country_iso2_from_m49,
    fuzzy_match,
    get_countries_by_region,
    get_countries_by_subregion,
    get_region_name
)
from django_countries.fields import Country
from django.conf import settings

settings.configure()


# Test data
world_regions = ["AQ", "BV", "IO", "CX", "CC", "TF", "HM", "GS", "UM"]
au_nz_subregions = ["AU", "NZ", "NF"]


class TestCountry(TestCase):
    def test_country_region(self):
        query = Country("AF").region
        self.assertEqual(query, 142)

    def test_country_region_name(self):
        query = Country("AF").region_name
        self.assertEqual(query, "Asia")

    def test_country_subregion(self):
        query = Country("AF").subregion
        self.assertEqual(query, 34)

    def test_country_subregion_name(self):
        query = Country("AF").subregion_name
        self.assertEqual(query, "Southern Asia")

    def test_invalid_country_region(self):
        query = Country("ZZ").region
        self.assertIsNone(query)

    def test_invalid_country_region_name(self):
        query = Country("ZZ").region_name
        self.assertIsNone(query)

    def test_invalid_country_subregion(self):
        query = Country("ZZ").subregion
        self.assertIsNone(query)

    def test_invalid_country_subregion_name(self):
        query = Country("ZZ").subregion_name
        self.assertIsNone(query)

    def test_is_sids(self):
        assert Country("AI").sids

    def test_is_not_sids(self):
        assert Country("GB").sids is False

    def test_is_ldc(self):
        assert Country("AF").ldc

    def test_is_not_ldc(self):
        assert Country("FR").ldc is False

    def test_is_lldc(self):
        assert Country("AM").lldc

    def test_is_not_lldc(self):
        assert Country("CH").lldc is False

    def test_get_preferred_name(self):
        assert Country("BE").preferred_name == "Belgium"
        assert Country("CD").preferred_name == "Democratic Republic of the Congo"

    def test_get_income_level(self):
        assert Country("AU").income_level == "High"
        assert Country("AF").income_level == "Low"
        assert Country("BG").income_level == "Upper middle"
        assert Country("CX").income_level is None

    def test_fuzzy_match_returns_exact_match(self):
        result = fuzzy_match("Burkina Faso")
        self.assertEqual(result, ("BF", True))

    def test_fuzzy_match_returns_fuzzy_match(self):
        result = fuzzy_match("Upper Volta")
        self.assertEqual(result, ("BF", False))

    def test_fuzzy_match_returns_no_match(self):
        result = fuzzy_match("Foobarland")
        self.assertEqual(result, (None, True))

    def test_m49_zero_returns_no_match(self):
        result = country_iso2_from_m49(0)
        self.assertEqual(result, None)

    def test_m49_valid_returns_match(self):
        result = country_iso2_from_m49(56)
        self.assertEqual(result, "BE")

    def test_m49_invalid_returns_no_match(self):
        result = country_iso2_from_m49(999999)
        self.assertEqual(result, None)


class TestRegions(TestCase):
    def test_countries_by_region(self):
        query = countries_by_region(2)
        assert len(query) == 60
        assert "DZ" in query

    def test_countries_by_subregion(self):
        query = countries_by_subregion(53)
        assert len(query) == 6
        assert "AU" in query

    def test_region_name(self):
        query = get_region_name(9)
        self.assertEqual(query, "Oceania")

    def test_subregion_name(self):
        query = get_region_name(53)
        self.assertEqual(query, "Australia and New Zealand")

    def test_invalid_countries_by_region(self):
        query = countries_by_region(900)
        self.assertIsNone(query)

    def test_invalid_countries_by_subregion(self):
        query = countries_by_subregion(999)
        self.assertIsNone(query)

    def test_invalid_region_name(self):
        query = get_region_name(900)
        self.assertIsNone(query)

    def test_returns_iso2_code_with_region(self):
        regions = get_countries_by_region()
        self.assertEqual("XF", regions[9]["iso2"])
        self.assertEqual(29, len(regions[9]["countries"]))

    def test_returns_iso2_code_with_sub_region(self):
        regions = get_countries_by_subregion()
        self.assertEqual("QP", regions[53]["iso2"])
        self.assertEqual(6, len(regions[53]["countries"]))
