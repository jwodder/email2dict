"""
Convert EmailMessage objects to dicts

Visit <https://github.com/jwodder/email2dict> for more information.
"""

__version__      = '0.1.0.dev1'
__author__       = 'John Thorvald Wodder II'
__author_email__ = 'email2dict@varonathe.org'
__license__      = 'MIT'
__url__          = 'https://github.com/jwodder/email2dict'

from datetime import datetime
import email
from email import headerregistry as hr
from email import policy
from email.message import EmailMessage, Message
from typing import Any, Dict, List, cast

__all__ = ["email2dict"]

def process_unique_string_header(ush: List[Any]) -> str:
    assert len(ush) == 1
    return str(ush[0])

def process_address(addr: hr.Address) -> Dict[str, str]:
    return {
        "realname": addr.display_name,
        "address": addr.addr_spec,
    }

def process_addr_headers(ahs: List[Any]) -> List[dict]:
    data: List[dict] = []
    for h in ahs:
        assert isinstance(h, hr.AddressHeader)
        for g in h.groups:
            addrlist: List[dict]
            if g.display_name is not None:
                group = {"group": g.display_name, "addresses": []}
                data.append(group)
                addrlist = cast(List[dict], group["addresses"])
            else:
                addrlist = data
            addrlist.extend(map(process_address, g.addresses))
    return data

def process_content_type_headers(cths: List[Any]) -> str:
    # Discard params
    ### TODO: Filter out certain params instead?
    assert len(cths) == 1
    assert isinstance(cths[0], hr.ContentTypeHeader)
    return cths[0].content_type

def process_date_headers(dh: List[Any]) -> List[datetime]:
    data = []
    for h in dh:
        assert isinstance(h, hr.DateHeader)
        data.append(h.datetime)
    return data

def process_unique_date_header(dh: List[Any]) -> datetime:
    assert len(dh) == 1
    assert isinstance(dh[0], hr.UniqueDateHeader)
    return dh[0].datetime

def process_unique_single_addr_header(ah: List[Any]) -> Dict[str, str]:
    assert len(ah) == 1
    assert isinstance(ah[0], hr.UniqueSingleAddressHeader)
    return process_address(ah[0].address)

def process_single_addr_header(ah: List[Any]) -> List[Dict[str, str]]:
    data = []
    for h in ah:
        assert isinstance(h, hr.SingleAddressHeader)
        data.append(process_address(h.address))
    return data

def process_content_disposition_header(cdh: List[Any]) -> Dict[str, Any]:
    assert len(cdh) == 1
    assert isinstance(cdh[0], hr.ContentDispositionHeader)
    return {
        "disposition": cdh[0].content_disposition,
        "params": dict(cdh[0].params),
    }

HEADER_PROCESSORS = {
    "subject": process_unique_string_header,
    "message-id": process_unique_string_header,
    "from": process_addr_headers,
    "to": process_addr_headers,
    "cc": process_addr_headers,
    "bcc": process_addr_headers,
    "content-type": process_content_type_headers,
    "date": process_unique_date_header,
    "resent-date": process_date_headers,
    "orig-date": process_unique_date_header,
    "resent-to": process_addr_headers,
    "resent-cc": process_addr_headers,
    "resent-bcc": process_addr_headers,
    "resent-from": process_addr_headers,
    "reply-to": process_addr_headers,
    "sender": process_unique_single_addr_header,
    "resent-sender": process_single_addr_header,
    "content-disposition": process_content_disposition_header,
}

SKIPPED_HEADERS = {
    "content-transfer-encoding",
    "mime-version",
}

def email2dict(msg: Message) -> Dict[str, Any]:
    if not isinstance(msg, EmailMessage):
        msg = message2email(msg)
    data: Dict[str, Any] = {"headers": {}}
    for header in msg.keys():
        header = header.lower()
        if header in SKIPPED_HEADERS:
            continue
        values = msg.get_all(header)
        if not values:
            continue
        elif header in HEADER_PROCESSORS:
            v = HEADER_PROCESSORS[header](values)
        else:
            v = list(map(str, values))
        data["headers"][header] = v
    data["preamble"] = msg.preamble
    if msg.is_multipart():
        data["content"] = list(map(email2dict, msg.iter_parts()))
    else:
        data["content"] = msg.get_content()
    data["epilogue"] = msg.epilogue
    return data

def message2email(msg: Message) -> EmailMessage:
    emsg = email.message_from_bytes(bytes(msg), policy=policy.default)
    assert isinstance(emsg, EmailMessage)
    return emsg