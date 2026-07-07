"""IPInfo CLient."""

__version__ = "0.1.2"

import dataclasses
import ipaddress
import json

import aiohttp


IPAddress = int | str | bytes | ipaddress.IPv4Address | ipaddress.IPv6Address


BASE_URL = "https://ipinfo.io"


class IPInfoError(Exception):
    """An error in the aioipinfo library."""


def parse_org(org: str) -> tuple[str, str]:
    """Split an "org" in an IPInfoResponse into an ASN and Name.

    Parameters
    ----------
    org : str
        The `IPInfoResponse.org` to parse.

    Returns
    -------
    tuple[str, str]
        The ASN Number and ASN Name respectively parsed from `org`.
    """

    return org.split(" ", maxsplit=1)


def parse_loc(loc: str) -> tuple[str, str]:
    """Split a lat,long pair str into a tuple.

    Parameters
    ----------
    loc : str
        The `IPInfoResponse.loc` to parse.

    Returns
    -------
    tuple[str, str]
        The lattitude and longitude respectively parsed from `loc`.
    """

    lat, long = loc.split(",", maxsplit=1)
    return lat.strip(), long.strip()


@dataclasses.dataclass
class IPInfoResponse:
    """The response object from an free ipinfo.io GeoLocation Data query.

    See ipinfo.io `docs`_ for property info.

    Exposes a `pprint` method that dumps the object to stdout.

    .. _docs: https://ipinfo.io/developers/data-types#geolocation-data
    """

    ip: str
    hostname: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    loc: str | None = None
    lat: str | None = None
    long: str | None = None
    org: str | None = None
    asn_num: str | None = None
    asn_name: str | None = None
    postal: str | None = None
    timezone: str | None = None

    def __post_init__(self):
        if self.org:
            self.asn_num, self.asn_name = parse_org(self.org)
        if self.loc:
            self.lat, self.long = parse_loc(self.loc)

    def pprint(self):
        """Pretty print this object."""

        print(json.dumps(dataclasses.asdict(self), indent=2, sort_keys=True))


class IPInfoClient:
    """A very simple client for the free ipinfo.io API.

    Parameters
    ----------
    token : str
        The `ipinfo.io` API token to use with requests.
    """

    def __init__(self, token: str) -> None:
        self.token = token
        self.params = {"token": self.token}
        self.headers = {
            "User-Agent": f"{aiohttp.http.SERVER_SOFTWARE} aioipinfo/{__version__}"
        }
        self.session = aiohttp.ClientSession(
            base_url=BASE_URL,
            headers=self.headers,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tback):
        await self.close()

    async def close(self):
        """Close the underlying session."""

        await self.session.close()

    async def ipinfo(self, address: IPAddress) -> IPInfoResponse:
        """Return ipinfo.io Geolocation Data information on the given IP address.

        Parameters
        ----------
        address : IPAddress
            The IP Address to query.

        Returns
        -------
        IPInfoResponse
            The parsed API response.

        Raises
        ------
        IPInfoError
            If any of the following exceptions occurred during the request -
            (json.JSONDecodeError, aiohttp.ClientError, TypeError, ValueError).
        """

        try:
            address = ipaddress.ip_address(address)
            resp = await self.session.get(
                f"/{address}", params=self.params, headers=self.headers
            )
            resp.raise_for_status()
            data = await resp.json()
            info = IPInfoResponse(**data)

        except aiohttp.ClientError as err:
            raise IPInfoError(f"Unable to get IP info: {err}") from err

        except (json.JSONDecodeError, TypeError) as err:
            raise IPInfoError(f"Invalid API response: {err}") from err

        except ValueError as err:
            raise IPInfoError(f"Not a valid address: {err}") from err

        return info
