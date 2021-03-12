import email
from email import policy
from email.generator import BytesGenerator
from email.headerregistry import Address, AddressHeader, Group
from email.message import EmailMessage, Message
from io import BytesIO
from mailbox import MMDFMessage, mboxMessage
from typing import Any, Dict, Iterable, List, Union
import attr

AddressOrGroup = Union[str, Address, Group]


@attr.s(auto_attribs=True)
class ContentType:
    maintype: str
    subtype: str
    params: Dict[str, Any] = attr.ib(factory=dict)

    @classmethod
    def parse(cls, s: str) -> "ContentType":
        """ Parse a :mailheader:`Content-Type` string """
        msg = EmailMessage()
        msg["Content-Type"] = s
        if msg["Content-Type"].defects:
            raise ValueError(s)
        ct = msg["Content-Type"]
        return cls(ct.maintype, ct.subtype, dict(ct.params))

    @property
    def content_type(self) -> str:
        return f"{self.maintype}/{self.subtype}"

    def __str__(self) -> str:
        ct = self.content_type
        msg = EmailMessage()
        msg["Content-Type"] = ct
        if msg["Content-Type"].defects:
            raise ValueError(ct)
        for k, v in self.params.items():
            msg.set_param(k, v)
        return str(msg["Content-Type"])

    def __bytes__(self) -> bytes:
        ct = self.content_type
        msg = EmailMessage()
        msg["Content-Type"] = ct
        if msg["Content-Type"].defects:
            raise ValueError(ct)
        for k, v in self.params.items():
            msg.set_param(k, v)
        return bytes(msg["Content-Type"])


def format_addresses(addresses: Iterable[AddressOrGroup]) -> str:
    """
    Format a sequence of addresses for use in a custom address header string
    """
    msg = EmailMessage()
    msg["To"] = [Address(addr_spec=a) if isinstance(a, str) else a for a in addresses]
    return str(msg["To"])


def parse_address(s: str) -> Address:
    msg = EmailMessage()
    msg["To"] = s
    if msg["To"].defects:
        raise ValueError(s)
    addresses: List[Address] = [
        address for group in msg["To"].groups for address in group.addresses
    ]
    if len(addresses) != 1:
        raise ValueError(s)
    return addresses[0]


def recipient_addresses(msg: EmailMessage) -> List[str]:
    recipients = set()
    for key in ["To", "CC", "BCC"]:
        for header in msg.get_all(key, []):
            assert isinstance(header, AddressHeader)
            for addr in header.addresses:
                recipients.add(addr.addr_spec)
    return sorted(recipients)


def message2email(msg: Message) -> EmailMessage:
    # Message.as_bytes() refolds long header lines (which can result in changes
    # in whitespace after reparsing) and doesn't give a way to change this, so
    # we need to use a BytesGenerator manually.
    fp = BytesIO()
    g = BytesGenerator(fp, mangle_from_=False, maxheaderlen=0)
    g.flatten(msg, unixfrom=msg.get_unixfrom() is not None)
    fp.seek(0)
    emsg = email.message_from_binary_file(fp, policy=policy.default)
    assert isinstance(emsg, EmailMessage)
    # MMDFMessage and mboxMessage make their "From " lines available though a
    # different method than normal Messages, so we have to copy it over
    # manually.
    if isinstance(msg, (MMDFMessage, mboxMessage)):
        emsg.set_unixfrom("From " + msg.get_from())
    return emsg