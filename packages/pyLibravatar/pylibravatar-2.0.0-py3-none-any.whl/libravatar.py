"""
pyLibravatar - Python module for Libravatar.

Easy way to make use of the federated Libravatar.org avatar hosting service
from within your Python applications.

Copyright (C) 2011, 2013, 2015 Francois Marier <francois@libravatar.org>
Copyright (C) 2016-2026 Oliver Falk <oliver@linux-kernel.at>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

import hashlib
import random
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import dns.resolver
from dns.rdtypes.IN.SRV import SRV

BASE_URL = "http://cdn.libravatar.org/avatar/"
SECURE_BASE_URL = "https://seccdn.libravatar.org/avatar/"
SERVICE_BASE = "_avatars._tcp"
SECURE_SERVICE_BASE = "_avatars-sec._tcp"
MIN_AVATAR_SIZE = 1
MAX_AVATAR_SIZE = 512


def libravatar_url(
    email: Optional[str] = None,
    openid: Optional[str] = None,
    https: bool = False,
    default: Optional[Union[str, int]] = None,
    size: Optional[Union[int, str]] = None,
) -> str:
    """Return a URL to the appropriate avatar."""
    avatar_hash: Optional[str]
    domain: Optional[str]
    avatar_hash, domain = parse_user_identity(email, openid)
    query_string = parse_options(default, size)

    delegation_server = lookup_avatar_server(domain, https)
    return compose_avatar_url(
        delegation_server, avatar_hash, query_string, https
    )


def parse_options(
    default: Optional[Union[str, int]], size: Optional[Union[int, str]]
) -> str:
    """Turn optional parameters into a query string."""
    query_string = ""
    if default:
        query_string = "?d=%s" % urllib.parse.quote_plus(str(default))
    if size:
        try:
            size = int(size)
        except ValueError:
            return query_string  # invalid size, skip

        if len(query_string) > 0:
            query_string += "&"
        else:
            query_string = "?"
        query_string += "s=%s" % max(
            MIN_AVATAR_SIZE, min(MAX_AVATAR_SIZE, size)
        )

    return query_string


def parse_user_identity(
    email: Optional[str], openid: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate user hash based on the email address or OpenID.

    The hash will be returned along with the relevant domain.
    """
    hash_obj = None
    if email:
        lowercase_value = email.strip().lower()
        domain = lowercase_value.split("@")[-1]
        hash_obj = hashlib.new("md5")
    elif openid:
        # pylint: disable=E1103
        url = urllib.parse.urlsplit(openid.strip())
        if url.username and url.hostname:
            password = url.password or ""
            netloc = url.username + ":" + password + "@" + url.hostname
        else:
            netloc = url.hostname or ""
        lowercase_value = urllib.parse.urlunsplit(
            (url.scheme.lower(), netloc, url.path, url.query, url.fragment)
        )
        domain = url.hostname or ""
        hash_obj = hashlib.new("sha256")

    if not hash_obj:  # email and openid both missing
        return (None, None)

    hash_obj.update(lowercase_value.encode("utf-8"))
    return (hash_obj.hexdigest(), domain)


def compose_avatar_url(
    delegation_server: Optional[str],
    avatar_hash: Optional[str],
    query_string: Optional[str],
    https: bool,
) -> str:
    """Assemble the final avatar URL based on the provided components."""
    avatar_hash = avatar_hash or ""
    query_string = query_string or ""

    base_url = BASE_URL
    if https:
        base_url = SECURE_BASE_URL

    if delegation_server:
        if https:
            base_url = "https://%s/avatar/" % delegation_server
        else:
            base_url = "http://%s/avatar/" % delegation_server

    return base_url + avatar_hash + query_string


def service_name(domain: Optional[str], https: bool) -> Optional[str]:
    """Return the DNS service to query for a given domain and scheme."""
    if not domain:
        return None

    if https:
        return "{}.{}".format(SECURE_SERVICE_BASE, domain)
    else:
        return "{}.{}".format(SERVICE_BASE, domain)


def lookup_avatar_server(domain: Optional[str], https: bool) -> Optional[str]:
    """
    Extract the avatar server from an SRV record in the DNS zone.

    The SRV records should look like this:

       _avatars._tcp.example.com.     IN SRV 0 0 80  avatars.example.com
       _avatars-sec._tcp.example.com. IN SRV 0 0 443 avatars.example.com
    """
    service = service_name(domain, https)
    if not service:
        return None
    try:
        answers = dns.resolver.resolve(service, "SRV")
    except dns.resolver.NXDOMAIN:
        return None
    except dns.resolver.NoAnswer:
        return None
    except Exception as e:
        print("DNS Error: %s" % e)
        return None

    records = []
    for rdata in answers:
        srv_rdata = cast(SRV, rdata)
        srv_record = {
            "priority": srv_rdata.priority,
            "weight": srv_rdata.weight,
            "port": srv_rdata.port,
            "target": str(srv_rdata.target),
        }

        records.append(srv_record)

    return normalized_target(records, https)


def normalized_target(
    records: List[Dict[str, Any]], https: bool
) -> Optional[str]:
    """
    Pick the right server to use and return its normalized hostname.

    The hostname will be returned but the port number will be omitted
    unless it's non-standard.
    """
    target, port = sanitize_target(srv_hostname(records))

    if target and ((https and port != 443) or (not https and port != 80)):
        return "{}:{}".format(target, port)

    return target


def sanitize_target(
    args: Tuple[Any, Any],
) -> Tuple[Optional[str], Optional[int]]:
    """Ensure we are getting a valid hostname and port from DNS resolver."""
    target, port = args

    if not target or not port:
        return (None, None)

    if not re.match("^[0-9a-zA-Z.-]+$", str(target)):
        return (None, None)

    try:
        if int(port) < 1 or int(port) > 65535:
            return (None, None)
    except ValueError:
        return (None, None)

    return (target, port)


def srv_hostname(
    records: List[Dict[str, Any]],
) -> Tuple[Optional[str], Optional[int]]:
    """Return the right (target, port) pair from a list of SRV records."""
    if len(records) < 1:
        return (None, None)

    if 1 == len(records):
        srv_record = records[0]
        return (srv_record["target"], srv_record["port"])

    # Keep only the servers in the top priority
    priority_records: List[Tuple[int, Dict[str, Any]]] = []
    total_weight = 0
    top_priority = records[0]["priority"]  # highest priority = lowest number

    for srv_record in records:
        if srv_record["priority"] > top_priority:
            # ignore the record (srv_record has lower priority)
            continue
        elif srv_record["priority"] < top_priority:
            # reset the array (srv_record has higher priority)
            top_priority = srv_record["priority"]
            total_weight = 0
            priority_records = []

        total_weight += srv_record["weight"]

        if srv_record["weight"] > 0:
            priority_records.append((total_weight, srv_record))
        else:
            # zero-weigth elements must come first
            priority_records.insert(0, (0, srv_record))

    if 1 == len(priority_records):
        srv_record = priority_records[0][1]
        return (srv_record["target"], srv_record["port"])

    # Select first record according to RFC2782 weight
    # ordering algorithm (page 3)
    random_number = random.randint(0, total_weight)

    for record in priority_records:
        weighted_index, srv_record = record

        if weighted_index >= random_number:
            return (srv_record["target"], srv_record["port"])

    print("There is something wrong with our SRV weight ordering algorithm")
    return (None, None)
