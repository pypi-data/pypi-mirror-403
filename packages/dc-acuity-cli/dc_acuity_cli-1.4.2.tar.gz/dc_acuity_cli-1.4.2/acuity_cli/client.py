"""Unified Acuity Scheduling API client.

Handles all API interactions with consistent error handling,
rate limiting, and retry logic.
"""

from __future__ import annotations

import logging
import time
from typing import Any, cast

import requests
from requests.auth import HTTPBasicAuth

from .config import API_BASE_URL, Config

logger = logging.getLogger(__name__)

# HTTP timeout in seconds
REQUEST_TIMEOUT = 10

# Rate limit retry settings
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # Exponential backoff multiplier

JSONDict = dict[str, Any]
JSONList = list[JSONDict]


class AcuityAPIError(Exception):
    """Acuity API error with code and details."""

    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        """Initialize API error.

        Args:
            code: Error code (e.g., AUTH_FAILED, NOT_FOUND)
            message: Human-readable error message
            details: Optional additional error details

        """
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"{code}: {message}")


class AcuityClient:
    """Client for Acuity Scheduling API."""

    def __init__(self, config: Config) -> None:
        """Initialize client with config.

        Args:
            config: Configuration with credentials

        """
        config.validate()
        self.config = config
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(config.user_id, config.api_key)
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> Any:
        """Make an API request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., /appointment-types)
            params: Query parameters
            json_data: JSON body for POST/PUT

        Returns:
            Parsed JSON response

        Raises:
            AcuityAPIError: On API errors

        """
        url = f"{API_BASE_URL}{endpoint}"
        logger.info(f"Fetching {endpoint}...")

        rate_limited = False
        last_retry_after: int | None = None

        def _safe_json(response: requests.Response) -> tuple[bool, Any]:
            if not response.text:
                return True, {}
            try:
                return True, response.json()
            except ValueError:
                return False, None

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    timeout=REQUEST_TIMEOUT,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    rate_limited = True
                    retry_after_header = response.headers.get("Retry-After")
                    retry_after = None
                    if retry_after_header:
                        try:
                            retry_after = int(retry_after_header)
                        except ValueError:
                            retry_after = None
                    wait_time = (
                        retry_after
                        if retry_after is not None
                        else RETRY_BACKOFF**attempt
                    )
                    last_retry_after = retry_after
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Rate limited, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    break

                # Handle auth errors
                if response.status_code == 401:
                    raise AcuityAPIError(
                        "AUTH_FAILED",
                        "Authentication failed - check credentials",
                    )

                # Handle not found
                if response.status_code == 404:
                    raise AcuityAPIError(
                        "NOT_FOUND",
                        f"Resource not found: {endpoint}",
                    )

                # Handle server errors with retry
                if response.status_code >= 500:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_BACKOFF**attempt
                        logger.warning(f"Server error, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise AcuityAPIError(
                        "SERVER_ERROR",
                        f"Server error: {response.status_code}",
                    )

                # Handle other client errors
                if response.status_code >= 400:
                    ok, error_data = _safe_json(response)
                    if not ok:
                        error_data = {"raw": response.text}
                        message = f"Error {response.status_code}"
                    elif not isinstance(error_data, dict):
                        raw_value = error_data
                        error_data = {"raw": raw_value}
                        message = (
                            str(raw_value)
                            if raw_value not in (None, "")
                            else f"Error {response.status_code}"
                        )
                    else:
                        message = error_data.get(
                            "message",
                            f"Error {response.status_code}",
                        )
                    raise AcuityAPIError("API_ERROR", message, error_data)

                # Success
                ok, data = _safe_json(response)
                if not ok:
                    raise AcuityAPIError(
                        "API_ERROR",
                        "Invalid JSON response from API",
                        {"raw": response.text},
                    )
                return data

            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    logger.warning("Request timeout, retrying...")
                    continue
                raise AcuityAPIError("TIMEOUT", "Request timed out")

            except requests.exceptions.ConnectionError:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF**attempt
                    logger.warning(f"Connection error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise AcuityAPIError("CONNECTION_ERROR", "Failed to connect to API")

        if rate_limited:
            if last_retry_after is not None:
                message = f"Rate limit exceeded. Retry after {last_retry_after}s."
            else:
                message = "Rate limit exceeded. Please retry later."
            raise AcuityAPIError("RATE_LIMITED", message)

        raise AcuityAPIError("MAX_RETRIES", "Max retries exceeded")

    # =========================================================================
    # Appointment Types
    # =========================================================================

    def list_appointment_types(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict]:
        """List all appointment types.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of appointment type objects with id, name, duration, calendarIDs

        """
        params: dict[str, int] = {}
        if limit is not None:
            params["max"] = limit
        if offset is not None:
            params["offset"] = offset

        result = cast(
            JSONList,
            self._request("GET", "/appointment-types", params=params or None),
        )
        logger.info(f"Found {len(result)} results")
        return result

    # =========================================================================
    # Calendars
    # =========================================================================

    def list_calendars(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict]:
        """List all calendars (team members).

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of calendar objects with id, name, email, etc.

        """
        params: dict[str, int] = {}
        if limit is not None:
            params["max"] = limit
        if offset is not None:
            params["offset"] = offset

        result = cast(
            JSONList,
            self._request("GET", "/calendars", params=params or None),
        )
        logger.info(f"Found {len(result)} results")
        return result

    # =========================================================================
    # Availability
    # =========================================================================

    def get_available_dates(
        self,
        appointment_type_id: int,
        month: str,
        calendar_id: int | None = None,
    ) -> list[dict]:
        """Get dates with availability in a month.

        Args:
            appointment_type_id: Appointment type ID (required)
            month: Month in YYYY-MM format
            calendar_id: Optional calendar filter

        Returns:
            List of date objects with available dates

        """
        params: dict[str, str | int] = {
            "appointmentTypeID": appointment_type_id,
            "month": month,
        }
        if calendar_id is not None:
            params["calendarID"] = calendar_id

        return cast(
            JSONList,
            self._request("GET", "/availability/dates", params=params),
        )

    def get_available_times(
        self,
        appointment_type_id: int,
        date: str,
        calendar_id: int | None = None,
    ) -> list[dict]:
        """Get available time slots for a specific date.

        Args:
            appointment_type_id: Appointment type ID (required)
            date: Date in YYYY-MM-DD format
            calendar_id: Optional calendar filter

        Returns:
            List of time slot objects with ISO-8601 times

        """
        params: dict[str, str | int] = {
            "appointmentTypeID": appointment_type_id,
            "date": date,
        }
        if calendar_id is not None:
            params["calendarID"] = calendar_id

        return cast(
            JSONList,
            self._request("GET", "/availability/times", params=params),
        )

    def check_time_slot(
        self,
        appointment_type_id: int,
        datetime_str: str,
        calendar_id: int | None = None,
    ) -> dict:
        """Validate a specific time slot before booking.

        Args:
            appointment_type_id: Appointment type ID (required)
            datetime_str: ISO-8601 datetime string
            calendar_id: Optional calendar filter

        Returns:
            Validation result with valid boolean and details

        """
        data: dict[str, object] = {
            "datetime": datetime_str,
            "appointmentTypeID": appointment_type_id,
        }
        if calendar_id is not None:
            data["calendarID"] = calendar_id

        try:
            result = self._request("POST", "/availability/check-times", json_data=data)
            return {"valid": True, "datetime": datetime_str, "result": result}
        except AcuityAPIError as e:
            return {
                "valid": False,
                "datetime": datetime_str,
                "reason": e.message,
            }

    # =========================================================================
    # Blocks
    # =========================================================================

    def create_block(
        self,
        start: str,
        end: str,
        calendar_id: int | None = None,
    ) -> dict:
        """Create a time block on a calendar.

        Args:
            start: Start datetime (ISO-8601)
            end: End datetime (ISO-8601)
            calendar_id: Optional calendar ID

        Returns:
            Block object

        """
        payload: dict[str, str | int] = {"start": start, "end": end}
        if calendar_id is not None:
            payload["calendarID"] = calendar_id
        return cast(JSONDict, self._request("POST", "/blocks", json_data=payload))

    # =========================================================================
    # Clients
    # =========================================================================

    def search_clients(
        self,
        search: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict]:
        """Search clients by name, email, or phone.

        Args:
            search: Partial match search string
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of matching client objects

        """
        params: dict[str, str | int] = {"search": search}
        if limit is not None:
            params["max"] = limit
        if offset is not None:
            params["offset"] = offset

        result = cast(JSONList, self._request("GET", "/clients", params=params))
        logger.info(f"Found {len(result)} results")
        return result

    def create_client(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Create a new client profile.

        Args:
            first_name: Client first name
            last_name: Client last name
            email: Client email address
            phone: Optional phone number
            notes: Optional internal notes

        Returns:
            Created client object

        Raises:
            AcuityAPIError: If client already exists (code: CLIENT_EXISTS)

        """
        data: dict[str, str] = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
        }
        if phone:
            data["phone"] = phone
        if notes:
            data["notes"] = notes

        try:
            return cast(JSONDict, self._request("POST", "/clients", json_data=data))
        except AcuityAPIError as e:
            if "already exists" in e.message.lower():
                raise AcuityAPIError(
                    "CLIENT_EXISTS",
                    f"Client with email {email} already exists",
                    e.details,
                )
            raise

    # =========================================================================
    # Appointments
    # =========================================================================

    def list_appointments(
        self,
        min_date: str | None = None,
        max_date: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict]:
        """List appointments with optional filters.

        Args:
            min_date: Start date filter (YYYY-MM-DD)
            max_date: End date filter (YYYY-MM-DD)
            first_name: Filter by client first name
            last_name: Filter by client last name
            email: Filter by client email
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of appointment objects

        """
        params: dict[str, str | int] = {}
        if min_date:
            params["minDate"] = min_date
        if max_date:
            params["maxDate"] = max_date
        if first_name:
            params["firstName"] = first_name
        if last_name:
            params["lastName"] = last_name
        if email:
            params["email"] = email
        if limit is not None:
            params["max"] = limit
        if offset is not None:
            params["offset"] = offset

        result = cast(JSONList, self._request("GET", "/appointments", params=params))
        logger.info(f"Found {len(result)} results")
        return result

    def get_appointment(self, appointment_id: int) -> dict:
        """Get details of a specific appointment.

        Args:
            appointment_id: Appointment ID

        Returns:
            Appointment object with full details

        """
        return cast(JSONDict, self._request("GET", f"/appointments/{appointment_id}"))

    def create_appointment(
        self,
        appointment_type_id: int,
        datetime_str: str,
        first_name: str,
        last_name: str,
        email: str,
        calendar_id: int | None = None,
        phone: str | None = None,
        notes: str | None = None,
        label_ids: list[int] | None = None,
        no_email: bool = False,
    ) -> dict:
        """Create a new appointment.

        Args:
            appointment_type_id: Appointment type ID (required)
            datetime_str: ISO-8601 datetime string (required)
            first_name: Client first name (required)
            last_name: Client last name (required)
            email: Client email (required)
            calendar_id: Optional specific calendar
            phone: Optional client phone
            notes: Optional appointment notes
            label_ids: Optional label IDs (Acuity supports a single label)
            no_email: Suppress confirmation email/SMS when True

        Returns:
            Created appointment object

        """
        data: dict[str, object] = {
            "appointmentTypeID": appointment_type_id,
            "datetime": datetime_str,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
        }
        if calendar_id is not None:
            data["calendarID"] = calendar_id
        if phone:
            data["phone"] = phone
        if notes:
            data["notes"] = notes
        if label_ids:
            data["labels"] = [{"id": label_id} for label_id in label_ids]

        params: dict[str, str] | None = None
        if no_email:
            params = {"noEmail": "true"}

        return cast(
            JSONDict,
            self._request(
                "POST",
                "/appointments",
                params=params,
                json_data=data,
            ),
        )

    def reschedule_appointment(
        self,
        appointment_id: int,
        datetime_str: str,
        calendar_id: int | None = None,
    ) -> dict:
        """Reschedule an existing appointment.

        Args:
            appointment_id: Appointment ID to reschedule
            datetime_str: New ISO-8601 datetime string
            calendar_id: Optional new calendar (auto-finds if omitted)

        Returns:
            Updated appointment object

        """
        data: dict[str, str | int] = {"datetime": datetime_str}
        if calendar_id is not None:
            data["calendarID"] = calendar_id

        return cast(
            JSONDict,
            self._request(
                "PUT",
                f"/appointments/{appointment_id}/reschedule",
                json_data=data,
            ),
        )

    def cancel_appointment(self, appointment_id: int) -> dict:
        """Cancel an appointment.

        Args:
            appointment_id: Appointment ID to cancel

        Returns:
            Cancelled appointment object

        """
        return cast(
            JSONDict,
            self._request("PUT", f"/appointments/{appointment_id}/cancel"),
        )
