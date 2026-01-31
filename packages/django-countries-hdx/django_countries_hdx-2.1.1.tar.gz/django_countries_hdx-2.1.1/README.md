# django-countries-hdx

This lib adds extra M49 data to django-countries.

It uses [hdx-python-country](https://github.com/OCHA-DAP/hdx-python-country) with the default data augmented by more UN data to provide SIDS, LLDC and LDC grouping data

## Installation

Install this library using `pip`:
```bash
pip install django-countries-hdx
```
## Usage

It adds extra properties to a `Country` for the region (id and name), sub-region (id and name), SIDS, LDC and LLDC.
It also contains helper methods to retrieve the countries in a region or sub-region.

```
>>> from django_countries.fields import Country
>>> from django_countries_hdx import regions
>>> Country('NZ').region
9
>>> Country("NZ").region_name
'Oceania'
>>> Country('NZ').subregion
53
>>> Country("NZ").subregion_name
'Australia and New Zealand'
>>> Country("AF").ldc
True
>>> Country("AF").lldc
True
>>> Country("AI").sids
True
>>> regions.get_region_name(9)
'Oceania'
>>> regions.get_region_name(53)
'Australia and New Zealand'
>>> regions.countries_by_region(9)
['AS',
 'AU',
 'CK',
 # …
 ]
>>> regions.countries_by_subregion(53)
['AU', 'NZ', 'NF']
```

## Development

To contribute to this library, first checkout the code. Then create a new virtual environment:
```bash
cd django-countries-hdx
python -m venv .venv
source .venv/bin/activate
```
Now install the test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
pytest
```

## Data updates

The data is a static file supplied with the lib. You can use the `data/merge.py` script to update this data.

Download the latest UN data to `data/unsd_methodology.csv` and run the script from the `data` dir. It will read the default `hdx` data and augment it with the UN data.

The merged result is then saved into the lib where it can be read back into the `hdx` lib.
