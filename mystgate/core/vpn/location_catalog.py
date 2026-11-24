from mystgate.core.mysterium import CountryLocation, IPType, MysteriumClient
from mystgate.core.vpn.models import CountryRow


class LocationCatalog:
    def __init__(self, client: MysteriumClient) -> None:
        """Initialize location queries over the Mysterium API client."""
        self.client = client

    def list_countries(self, ip_type: IPType | None = None) -> list[CountryRow]:
        """List countries with merged available cities, availability, and IP types."""
        requested_types = [ip_type] if ip_type is not None else [IPType.RESIDENTIAL, IPType.HOSTING]
        merged: dict[str, tuple[str, set[str], bool, list[IPType]]] = {}

        for current_type in requested_types:
            locations: list[CountryLocation] = self.client.list_locations(current_type)
            for location in locations:
                code = location.country.upper()
                name = location.display_name()
                available_cities = {city.display_name() for city in location.cities if city.is_available}
                if code not in merged:
                    merged[code] = (name, set(available_cities), location.is_available, [current_type])
                    continue

                prev_name, prev_cities, prev_available, prev_types = merged[code]
                prev_cities.update(available_cities)
                if current_type not in prev_types:
                    prev_types.append(current_type)
                merged[code] = (prev_name, prev_cities, prev_available or location.is_available, prev_types)

        return [
            CountryRow(
                code=code,
                name=name,
                cities=sorted(cities),
                available=available,
                ip_types=types,
            )
            for code, (name, cities, available, types) in sorted(merged.items())
        ]
