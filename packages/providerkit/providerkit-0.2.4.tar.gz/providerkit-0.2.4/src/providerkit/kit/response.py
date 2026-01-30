import csv
import json
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable

from qualitybase.services.utils import format_tabulate


class ResponseMixin:
    """Mixin for handling responses."""

    def response(self, service_name: str, raw: bool = False, format: str | None = None) -> str:
        if raw:
            get_result: Callable[[str], Any] = cast('Callable[[str], Any]', getattr(self, 'get_service_result', lambda _: ''))
            result = get_result(service_name)
            return str(result)
        if format and hasattr(self, f'response_{format}'):
            return str(getattr(self, f'response_{format}')(service_name))
        get_normalize: Callable[[str], Any] = cast('Callable[[str], Any]', getattr(self, 'get_service_normalize', lambda _: ''))
        normalize = get_normalize(service_name)
        return str(normalize)

    def response_terminal(self, service_name: str) -> str:
        """Response in terminal."""
        get_normalize: Callable[[str], Any] = cast('Callable[[str], Any]', getattr(self, 'get_service_normalize', lambda _: {}))
        response: Any = get_normalize(service_name)
        return str(format_tabulate(response, empty_message='No data available.'))

    def response_json(self, service_name: str) -> str:
        get_normalize: Callable[[str], Any] = cast('Callable[[str], Any]', getattr(self, 'get_service_normalize', lambda _: {}))
        response: Any = get_normalize(service_name)
        return json.dumps(response, indent=2, ensure_ascii=False)

    def response_xml(self, service_name: str) -> str:
        """Convert response to XML format."""
        get_normalize: Callable[[str], Any] = cast('Callable[[str], Any]', getattr(self, 'get_service_normalize', lambda _: {}))
        response: Any = get_normalize(service_name)

        def sanitize_xml_name(name: str) -> str:
            """Convert a string to a valid XML element name."""
            import re

            name = str(name).strip()
            if not name:
                return 'item'
            name = re.sub(r'[^a-zA-Z0-9_\-:.]', '_', name)
            if name[0].isdigit():
                name = f'_{name}'
            return name

        def dict_to_xml(data: Any, parent: ET.Element) -> None:
            if isinstance(data, dict):
                for key, value in data.items():
                    xml_name = sanitize_xml_name(key)
                    elem = ET.SubElement(parent, xml_name)
                    if xml_name != key:
                        elem.set('original_name', key)
                    dict_to_xml(value, elem)
            elif isinstance(data, list):
                for item in data:
                    elem = ET.SubElement(parent, 'item')
                    dict_to_xml(item, elem)
            else:
                parent.text = str(data) if data is not None else ''

        root = ET.Element('response')
        dict_to_xml(response, root)
        ET.indent(root)
        return ET.tostring(root, encoding='unicode')

    def response_csv(self, service_name: str) -> str:
        """Convert response to CSV format."""
        import io

        get_normalize: Callable[[str], Any] = cast('Callable[[str], Any]', getattr(self, 'get_service_normalize', lambda _: {}))
        response: Any = get_normalize(service_name)
        output = io.StringIO()
        writer = csv.writer(output)

        if isinstance(response, list):
            if not response:
                return ''
            if isinstance(response[0], dict):
                headers = list(response[0].keys())
                writer.writerow(headers)
                for item in response:
                    writer.writerow([item.get(k, '') for k in headers])
            else:
                writer.writerow(response)
        elif isinstance(response, dict):
            for key, value in sorted(response.items()):
                writer.writerow([key, value])
        else:
            writer.writerow([str(response)])

        return output.getvalue()
