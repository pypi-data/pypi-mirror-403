import re
import unicodedata

from urllib.parse import quote, unquote, urlencode

import can_ada


SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def normalize_url(url: str, default_scheme: str = "https") -> str:
    """
    Transforms the raw_url with following rules:
    * Lowercase hostname
    * Lowercase schema
    * Remove default ports
    * Uppercase the percent-encoding
    * Remove trailing slashes in path
    * Remove trailing dots at end of hostnames
    * Sort query parameters:
      * sort names and then values as case sensitive strings
      * keep order of arrays ( example: "a[]=y&a[]=x" )
    * Decode international characters and UTF8
    * Normalize UTF8 with "NFKC" rules
    * percent-encode reserved characters if needed:
      * reserved characters are defined in https://datatracker.ietf.org/doc/html/rfc3986#section-2.2
      * these characters are encoded if they appear in places other than defined in https://www.rfc-editor.org/rfc/rfc3986.html
      * mainly, the path or query parts of URL are affected

    Uses can-ada url parser (https://pypi.org/project/can-ada/).
    It is compliant with the standard https://url.spec.whatwg.org/
    and  ~4x faster than urllib
    """
    url = unicodedata.normalize("NFKC", url)

    if not SCHEME_RE.match(url):
        if not default_scheme:
            raise ValueError("default_scheme must not be empty")
        url = f"{default_scheme}://{url.lstrip('/')}"

    parsed_url = can_ada.parse(url)
    assert parsed_url.hostname

    # Ada (can_ada) validates values in setters and silently ignores invalid
    # Below we ensure that the value was set and not silently ignored
    hostname = parsed_url.hostname.rstrip(".")
    parsed_url.hostname = hostname
    assert parsed_url.hostname == hostname

    pathname = quote(unquote(parsed_url.pathname)).rstrip("/") or "/"
    parsed_url.pathname = pathname
    assert parsed_url.pathname == pathname

    search = _normalize_url_query(parsed_url.search)
    parsed_url.search = search
    assert parsed_url.search == search

    return str(parsed_url)


def _normalize_url_query_sort_key(key_value):
    key, value = key_value
    if "[]" in key:
        return f"{key}="
    else:
        return f"{key}={value}"


def _normalize_url_query(raw_url_query: str) -> str:
    url_query = raw_url_query.lstrip("?")
    if not url_query:
        return ""
    filtered_query = [
        (key, value)
        for key, value in list(can_ada.URLSearchParams(url_query))
        if not key.startswith("utm_")
    ]
    sorted_query = sorted(filtered_query, key=_normalize_url_query_sort_key)
    if not sorted_query:
        return ""

    return "?" + urlencode(sorted_query)


def clean_url(url, keep_www=False):
    """
    Format and clean an url to be saved or checked.
    Args:
        url: url to be formatted
        keep_www: keep the 'www' part of the url
    Returns: formatted url
    """

    url = url.strip()
    url = url.replace("https://", "").replace("http://", "").rstrip("/")
    if not keep_www:
        url = url.replace("www.", "")
    split_url = url.split("/")
    split_url[0] = split_url[0].lower()
    return "/".join(split_url)


def get_clean_domain(url):
    """
    Format and clean an url and returns domain.
    Args:
        url: url to be formatted
    Returns: formatted domain
    """

    return clean_url(url).split("/")[0]
