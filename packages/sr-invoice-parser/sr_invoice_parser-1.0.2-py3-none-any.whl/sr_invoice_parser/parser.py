from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Tuple, Union
from urllib.parse import urlparse

import pytz
import requests
from parsel import Selector
from srtools import cyrillic_to_latin

from .decorators import handle_exception
from .exceptions import ParserParseException, ParserRequestException


class InvoiceParser:
    ALLOWED_DOMAINS = ["suf.purs.gov.rs"]
    DATETIME_FORMAT = "%d.%m.%Y. %H:%M:%S"
    REQUEST_TIMEOUT = 30
    VAT_MAP = {"a": 0, "e": 10, "g": 0, "đ": 20}

    def __init__(
        self,
        url: Optional[str] = None,
        html_text: Optional[str] = None,
        json: bool = True,
    ) -> None:
        if not url and not html_text:
            raise ParserParseException("URL or HTML content is required")

        self.url = url
        self.html_text = html_text
        self.json_data = None
        self.html_selector = None
        self.use_json = json

        if url and not html_text:
            self.fetch()
        else:
            self.html_selector = self.get_html_selector(self.html_text)

    def validate_url(self) -> None:
        """Validate the URL to ensure it's from an allowed domain"""
        parsed_url = urlparse(self.url)

        if parsed_url.netloc not in self.ALLOWED_DOMAINS:
            raise ParserRequestException("Invalid domain")

    @handle_exception()
    def get_html_selector(self, html_text: Union[str, bytes]) -> Selector:
        if isinstance(html_text, bytes):
            return Selector(body=html_text)
        return Selector(text=html_text)

    def fetch(self) -> None:
        """Fetch content from the URL (JSON or HTML based on use_json flag)"""

        self.validate_url()

        headers = {"Accept": "application/json"} if self.use_json else None
        try:
            response = requests.get(
                self.url, headers=headers, timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            raise ParserRequestException(f"Request failed: {e}")
        except requests.RequestException as e:
            raise ParserRequestException(f"Request failed: {e}")

        if self.use_json:
            self.json_data = response.json()
        else:
            self.html_selector = self.get_html_selector(response.content)

    @handle_exception()
    def get_company_name(self) -> str:
        """Get the company name"""

        if self.json_data:
            value = self.json_data["invoiceRequest"]["businessName"]
        else:
            value = self.html_selector.css("span#shopFullNameLabel::text").get().strip()
        return value

    @handle_exception()
    def get_company_tin(self) -> str:
        """Get the company tin/tax identification number"""

        if self.json_data:
            value = self.json_data["invoiceRequest"]["taxId"]
        else:
            value = self.html_selector.css("span#tinLabel::text").get().strip()
        return value

    @handle_exception()
    def get_buyer_tin(self) -> Optional[str]:
        """Get the buyer tin/tax identification number"""

        if self.json_data:
            buyer = self.json_data["invoiceRequest"].get("buyer")
            return buyer if buyer else None
        value = self.html_selector.css("span#buyerIdLabel::text").get().strip()
        if value:
            parts = value.split(":")
            if len(parts) == 2:
                return parts[1]
        return None

    def string_to_float(self, string: str) -> float:
        return float(string.replace(".", "").replace(",", "."))

    @handle_exception()
    def get_total_amount(self) -> float:
        """Get the total amount of the invoice"""

        if self.json_data:
            value = self.json_data["invoiceResult"]["totalAmount"]
        else:
            value = self.string_to_float(
                self.html_selector.css("span#totalAmountLabel::text").get().strip()
            )
        return value

    @handle_exception()
    def get_dt(self) -> datetime:
        """Get the datetime of the invoice"""

        if self.json_data:
            sdc_time = self.json_data["invoiceResult"]["sdcTime"]
            # Handle ISO format like '2023-01-03T10:15:33.93Z'
            dt = datetime.fromisoformat(sdc_time.replace("Z", "+00:00"))
            return dt.astimezone(pytz.utc)

        value = self.html_selector.css("span#sdcDateTimeLabel::text").get().strip()

        dt = datetime.strptime(value, self.DATETIME_FORMAT)
        belgrade_tz = pytz.timezone("Europe/Belgrade")
        dt_in_belgrade = belgrade_tz.localize(dt)
        return dt_in_belgrade.astimezone(pytz.utc)

    @handle_exception()
    def get_invoice_number(self) -> str:
        """Get the invoice number"""

        if self.json_data:
            value = self.json_data["invoiceResult"]["invoiceNumber"]
        else:
            value = (
                self.html_selector.css("span#invoiceNumberLabel::text").get().strip()
            )
        return value

    @handle_exception()
    def get_invoice_text(self) -> str:
        """Get the invoice text"""

        if self.json_data:
            value = self.json_data["journal"]
        else:
            value = self.html_selector.css("div#collapse3 > div > pre").get().strip()
        return value

    def get_name_and_vat_from_item_string(self, item_string: str) -> Tuple[str, int]:
        """Extract the item name and VAT rate from an item string."""
        item_string = cyrillic_to_latin(item_string).strip()
        item_string_lower = item_string.lower().strip()
        vat = 0

        if len(item_string_lower) >= 3 and item_string_lower[-3] == "(":
            vat_char = item_string_lower[-2]
            vat = self.VAT_MAP.get(vat_char, 20)
            item_string = item_string[:-3]

        return item_string.strip(), vat

    @handle_exception()
    def get_items(self, invoice_text: Union[str, None] = None) -> list[dict]:
        """Get all the items from the invoice as array of objects"""

        if not invoice_text:
            invoice_text = self.get_invoice_text()
        invoice_items = (
            invoice_text.split("========================================")[1]
            .split("----------------------------------------")[0]
            .split("Укупно")[1]
            .strip()
        )
        if "\r\n" in invoice_items:
            invoice_items = invoice_items.split("\r\n")
        elif "\n" in invoice_items:
            invoice_items = invoice_items.split("\n")

        items = []
        new_item = True
        for item in invoice_items:
            item = re.sub(" +", " ", item)
            if new_item:
                data = {
                    "name": item,
                    "vat": None,
                    "price": None,
                    "quantity": None,
                    "total_price": None,
                }
                items.append(data)
                new_item = False
            else:
                row_array = item.split()

                try:
                    # if the row is a number, then name is finished and we update price and quantity
                    price = self.string_to_float(row_array[0])
                    quantity = int(row_array[1])
                    total_price = self.string_to_float(row_array[2])
                    item, vat = self.get_name_and_vat_from_item_string(
                        items[-1]["name"]
                    )

                    items[-1]["name"] = item
                    items[-1]["vat"] = vat
                    items[-1]["price"] = price
                    items[-1]["quantity"] = quantity
                    items[-1]["total_price"] = total_price

                    new_item = True
                except ValueError:
                    # row is part of the item name, append it to the name
                    # if item.startswith(" "):
                    # items[-1]["name"] += ""
                    items[-1]["name"] += item

        return items

    def data(self) -> dict:
        """Parse and return the data from the invoice"""

        company_name = self.get_company_name()
        company_tin = self.get_company_tin()
        buyer_tin = self.get_buyer_tin()
        total_amount = self.get_total_amount()
        invoice_number = self.get_invoice_number()
        invoice_text = self.get_invoice_text()
        invoice_items = self.get_items(invoice_text)
        dt = self.get_dt()
        return {
            "company_name": company_name,
            "company_tin": company_tin,
            "buyer_tin": buyer_tin,
            "invoice_number": invoice_number,
            "invoice_datetime": dt,
            "invoice_total_amount": total_amount,
            "invoice_items": invoice_items,
            "invoice_text": invoice_text,
        }
