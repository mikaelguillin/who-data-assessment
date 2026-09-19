from pipeline.adapters.base import AdapterResult, CountryAdapter
from pipeline.adapters.country_a import CountryAAdapter
from pipeline.adapters.country_b import CountryBAdapter
from pipeline.adapters.country_c import CountryCAdapter

ADAPTERS: list[CountryAdapter] = [
    CountryAAdapter(),
    CountryBAdapter(),
    CountryCAdapter(),
]

__all__ = ["ADAPTERS", "AdapterResult", "CountryAdapter"]
