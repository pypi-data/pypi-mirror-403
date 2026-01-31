"""Provision Timeseries Builder"""

from typing import Any

from opengate_data.searching.search import SearchBuilder
from opengate_data.utils.utils import (
    send_request,
    set_method_call,
    parse_json,
    validate_type,
    validate_build_method_calls_execute,
    validate_build,
    build_headers,
)

class TimeseriesBuilder(SearchBuilder):
    """ Class timeseries builder """

    def __init__(self, opengate_client):
        super().__init__()
        self.client = opengate_client

        if self.client.url is None:
            self.base_url = "https://frontend:8443/v80/provision/organization"
        else:
            self.base_url = f"{self.client.url}/north"

        self.organization_name: str | None = None
        self.identifier: str | None = None
        self.callback_url: str | None = None
        self.method: str | None = None
        self.method_calls: list = []

    @set_method_call
    def with_organization_name(self, organization_name: str) -> "TimeseriesBuilder":
        validate_type(organization_name, str, "organization_name")
        self.organization_name = organization_name
        return self

    @set_method_call
    def with_identifier(self, identifier: str) -> "TimeseriesBuilder":
        validate_type(identifier, str, "identifier")
        self.identifier = identifier
        return self

    @set_method_call
    def with_callback(self, callback_url: str) -> "TimeseriesBuilder":
        validate_type(callback_url, str, "callback")
        self.callback_url = callback_url
        return self

    @set_method_call
    def with_output_file(
        self,
        filename: str,
        content_type: str | None = None,
    ) -> "TimeseriesBuilder":
        validate_type(filename, str, "outputFile.name")

        if content_type is None:
            content_type = "application/vnd.apache.parquet"
        else:
            validate_type(content_type, str, "outputFile.contentType")

        self.body_data.setdefault("outputFile", {})
        self.body_data["outputFile"]["name"] = filename
        self.body_data["outputFile"]["contentType"] = content_type
        return self
    
    @set_method_call
    def export(self) -> "TimeseriesBuilder":
        self.method = "export"
        return self

    @set_method_call
    def export_status(self) -> "TimeseriesBuilder":
        self.method = "status"
        return self

    @set_method_call
    def build(self) -> "TimeseriesBuilder":
        self._validate_builds()
        return self

    @set_method_call
    def build_execute(self):
        if "build" in self.method_calls:
            raise ValueError(
                "You cannot use 'build_execute()' together with 'build()'"
            )

        if "execute" in self.method_calls:
            raise ValueError(
                "You cannot use 'build_execute()' together with 'execute()'"
            )

        self._validate_builds()
        return self.execute()

    @set_method_call
    def execute(self) -> Any:
        validate_build_method_calls_execute(self.method_calls)

        url = (
            f"{self.base_url}/v80/timeseries/provision/organizations/"
            f"{self.organization_name}/{self.identifier}/export"
        )

        methods = {
            "export": self._execute_export,
            "status": self._execute_status,
        }

        func = methods.get(self.method)
        if func is None:
            raise ValueError(f"Unsupported method: {self.method!r}")

        return func(url)

    def _execute_export(self, url: str) -> dict[str, Any]:
        body = self.body_data or {}

        headers = build_headers(self.client.headers)
        if self.callback_url:
            headers["callback"] = self.callback_url

        response = send_request(
            method="post",
            headers=headers,
            url=url,
            json_payload=body,
        )

        result = {"status_code": response.status_code}

        if response.status_code == 202:
            result["data"] = (
                "Export request has been accepted and it's currently "
                "being exported in the background."
            )
        elif response.status_code == 204:
            result["data"] = "The selected timeseries has no data"
        elif response.status_code == 409:
            result["data"] = (
                "This timeseries is currently being exported by another process"
            )
        else:
            if response.text:
                result["error"] = response.text

        return result

    def _execute_status(self, url: str) -> dict[str, Any]:
        import time

        headers = build_headers(self.client.headers, accept="application/json")
        if self.callback_url:
            headers["callback"] = self.callback_url

        max_attempts = 10
        delay_seconds = 2

        response = None
        for _ in range(max_attempts):
            response = send_request(
                method="get",
                headers=headers,
                url=url,
            )

            if response.status_code != 406:
                break

            time.sleep(delay_seconds)

        result = {"status_code": response.status_code}

        if response.status_code == 200:
            result["data"] = parse_json(response.text)
        else:
            if response.text:
                result["error"] = response.text

        return result

    def _validate_builds(self):
        state = {
            "organization_name": self.organization_name,
            "identifier": self.identifier,
            "callback_url": self.callback_url,
            "body_data": self.body_data if self.body_data else None,
        }

        spec = {
            "export": {
                "required": ["organization_name", "identifier"],
                "forbidden": [],
            },
            "status": {
                "required": ["organization_name", "identifier"],
                "forbidden": ["body_data"],
            },
        }

        allowed_method_calls = {"export", "export_status"}

        field_aliases = {
            "organization_name": "with_organization_name",
            "identifier": "with_identifier",
            "callback_url": "with_callback",
            "body_data": "with_filter / with_select / with_limit / with_output_file",
        }

        method_aliases = {
            "export": "export()",
            "status": "export_status()",
        }

        validate_build(
            method=self.method,
            state=state,
            spec=spec,
            used_methods=self.method_calls,
            allowed_method_calls=allowed_method_calls,
            field_aliases=field_aliases,
            method_aliases=method_aliases,
        )

        return self
