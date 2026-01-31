import requests
from datetime import datetime
from eigeningenuity.core import get_default_server, EigenServer
from eigeningenuity.util import (
    force_list,
    get_eigenserver,
    parseEvents,
    _do_chunked_eigen_post_request,
    _do_eigen_post_request,
    validate_eventlog_query,
)

from typing import Union


class EventLog(object):
    """An elasticsearch instance which talks the Eigen elastic endpoint."""

    def __init__(self, baseurl: str, default_eventlog: str, auth: bool):
        """This is a constructor. It takes in a URL like http://infra:8080/ei-applet/search/"""
        self.baseurl = baseurl
        self.eigenserver = get_eigenserver(baseurl)
        self.auth = auth
        self.default_eventlog = default_eventlog

    def _testConnection(self):
        """Preflight Request to verify connection to ingenuity"""
        try:
            status = requests.get(self.baseurl, verify=False).status_code
        except ConnectionError:
            raise ConnectionError(
                "Failed to connect to ingenuity instance at "
                + self.eigenserver
                + ". Please check the url is correct and the instance is up."
            )

    def _doJsonWriteRequest(self, relative_url: str, data: dict, label: str):
        url = self.baseurl + relative_url
        return _do_chunked_eigen_post_request(url, data, label, self.auth)

    def _doJsonReadRequest(self, relative_url: str, data: dict):
        url = self.baseurl + relative_url
        response = _do_eigen_post_request(url, data, self.auth)

        if response["success"] is not True:
            raise ValueError("Query failed: " + str(response["errors"]))

        return response["response"]

    def getEvents(
        self, query: dict, eventlog: str = "default", size: int = 1000, page: int = 0
    ) -> list:
        """
        Execute a raw query against the ingenuity eventlog

        Args:
            query: A dictionary containing the query structure with the following format:
                - start (required): Start time (e.g., "yesterday", SO datetime string, python datetime object)
                - end (required): End time (e.g., "now", SO datetime string, python datetime object)
                - severities (optional): List of severity levels (e.g., ["INFO", "WARNING"])
                - types (optional): List of event types (e.g., ["DataTagThresholdCheck"]). Exact matches only. API fails to parse certain characters like '-'
                - sources (optional): List of source identifiers. Allows partial matches
                - messages (optional): List of message types. Allows partial matches
                - assetNames (optional): List of asset names
                - contentFilter (optional): Additional filter string. Uses Elasticsearch Query String syntax e.g. (fieldName1 = value1 AND fieldName2 = value2) AND (fieldName3 = b OR fieldName4 = d)
            size: Maximum number of results to return (default: 1000)
            page: Page number for pagination (default: 0)

        Returns:
            The response from ingenuity, typically a list of dictionaries

        Raises:
            ValueError: If required fields are missing or invalid
        """

        if eventlog == "default":
            eventlog = self.default_eventlog

        # Validate the query structure and required fields
        validate_eventlog_query(query)

        relative_url = f"/list/{eventlog}"
        body = {"request": query, "size": size, "page": page}

        response = self._doJsonReadRequest(relative_url, body)

        return response

    def getEventsBySource(
        self,
        source: Union[str, list],
        eventlog: str = "default",
        exact_match: bool = False,
        start: Union[str, datetime] = "yesterday",
        end: Union[str, datetime] = "now",
        filter: Union[str, None] = None,
        size: int = 1000,
        page: int = 0,
    ) -> list:
        """
        Retrieve events from the ingenuity eventlog filtered by source

        Args:
            source: The source identifier to filter events by (string)
            exact_match: If True, only return events with an exact match on source. If False, allows partial matches (default: False)
            start: Start time (e.g., "yesterday", SO datetime string, python datetime object)
            end: End time (e.g., "now", SO datetime string, python datetime object)
            filter: Additional filter string. Uses Elasticsearch Query String syntax e.g. (fieldName1 = value1 AND fieldName2 = value2) AND (fieldName3 = b OR fieldName4 = d) (default: None)
            size: Maximum number of results to return (default: 1000)
            page: Page number for pagination (default: 0)

        Returns:
            The response from ingenuity, typically a list of dictionaries

        Raises:
            ValueError: If the source is not provided
        """
        if not source or not isinstance(source, (str, list)):
            raise ValueError("Source must be a non-empty string or list")

        source = force_list(source)

        if eventlog == "default":
            eventlog = self.default_eventlog

        validate_eventlog_query({"start": start, "end": end, "sources": source})

        relative_url = f"/list/{eventlog}"
        body = {
            "request": {"start": start, "end": end, "sources": source},
            "size": size,
            "page": page,
        }

        # Only include contentFilter if it's not None
        if filter is not None:
            body["request"]["contentFilter"] = filter

        response = self._doJsonReadRequest(relative_url, body)

        if exact_match:
            # Filter results to only include exact matches on source
            filtered_events = [
                event for event in response["items"] if event.get("source") in source
            ]
            return filtered_events

        return response

    def getEventsByType(
        self,
        event_type: Union[str, list],
        eventlog: str = "default",
        start: Union[str, datetime] = "yesterday",
        end: Union[str, datetime] = "now",
        filter: Union[str, None] = None,
        size: int = 1000,
        page: int = 0,
    ) -> list:
        """
        Retrieve events from the ingenuity eventlog filtered by event type

        Args:
            event_type: The event type to filter events by (string)
            start: Start time (e.g., "yesterday", ISO datetime string, python datetime object)
            end: End time (e.g., "now", ISO datetime string, python datetime object)
            filter: Additional filter string. Uses Elasticsearch Query String syntax e.g. (fieldName1 = value1 AND fieldName2 = value2) AND (fieldName3 = b OR fieldName4 = d) (default: None)
            size: Maximum number of results to return (default: 1000)
            page: Page number for pagination (default: 0)

        Returns:
            The response from ingenuity, typically a list of dictionaries

        Raises:
            ValueError: If the event type is not provided
        """
        if not event_type or not isinstance(event_type, (str, list)):
            raise ValueError("Event type must be a non-empty string or list")

        event_type = force_list(event_type)

        if eventlog == "default":
            eventlog = self.default_eventlog

        validate_eventlog_query({"start": start, "end": end, "types": event_type})

        relative_url = f"/list/{eventlog}"
        body = {
            "request": {"start": start, "end": end, "types": event_type},
            "size": size,
            "page": page,
        }

        # Only include contentFilter if it's not None
        if filter is not None:
            body["request"]["contentFilter"] = filter

        response = self._doJsonReadRequest(relative_url, body)

        return response

    def getEventsById(
        self,
        event_ids: Union[str, list],
        id_type: str = "eventId",
        eventlog: str = "default",
    ) -> list:
        """
        Retrieve events from the ingenuity eventlog filtered by event IDs

        Args:
            event_ids: A single event ID (string) or a list of event IDs to retrieve
            id_type: The type of ID to filter by
                "eventId" - Filter by the unique event identifier generated by ingenuity
                "externalId" - Filter by an unique identifier assign by uploader
                "episodeId" - Filter by the episode identifier associated with event pairs (Start/End)
                (default: "eventId")
            eventlog: The name of the eventlog to query (default: default_eventlog)


        Returns:
            The response from ingenuity, typically a list of dictionaries
        Raises:
            ValueError: If event_ids is not provided
        """

        if not event_ids or not isinstance(event_ids, (str, list)):
            raise ValueError("Event IDs must be a non-empty string or list")
        event_ids = force_list(event_ids)

        # Most id types return one event per id
        size = len(event_ids)

        match id_type:
            case "eventId":
                id_type = "eventIds"
            case "externalId":
                id_type = "eventExternalIds"
            case "episodeId":
                id_type = "episodeIds"
                size *= 2  # Each episode can have a start and end event
            case _:
                raise ValueError(
                    "id_type must be one of: eventId, externalId, episodeId"
                )

        if eventlog == "default":
            eventlog = self.default_eventlog

        relative_url = f"/list/{eventlog}"
        body = {
            "request": {
                id_type: event_ids,
                "start": "1970-01-01T00:00:00.000Z",
                "end": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            },
            "size": size,
            "page": 0,
        }

        response = self._doJsonReadRequest(relative_url, body)

        return response

    def deleteEventsById(
        self, event_ids: Union[str, list], eventlog: str = "default"
    ) -> bool:
        """
        Delete events from the ingenuity eventlog filtered by event IDs

        Args:
            event_ids: A single event ID (string) or a list of event IDs to delete
            eventlog: The name of the eventlog to query (default: default_eventlog)
        """

        if not event_ids or not isinstance(event_ids, (str, list)):
            raise ValueError("Event IDs must be a non-empty string or list")
        event_ids = force_list(event_ids)

        if eventlog == "default":
            eventlog = self.default_eventlog

        relative_url = f"/delete/{eventlog}"

        failed_ids = []

        for event_id in event_ids:
            event_url = f"{relative_url}?eventId={event_id}&flush=true"
            response = self._doJsonDeleteRequest(event_url)

            if not response:
                failed_ids.append(event_id)

        if failed_ids:
            return {
                "success": False,
                "errors": {"failed to delete events with ids": failed_ids},
            }
        else:
            return {"success": True, "errors": {}}

    def pushToEventlog(self, events: Union[dict, list]) -> bool:
        """
        Push one or more events to the ingenuity eventlog, accepts any event structure

        Args:
            events: A single event as dict, many events as a list of dicts, or the string filepath of a file containing events

        Returns:
            A boolean representing the successful push of all events. False if at least one event failed to be created
        """
        events = parseEvents(events)
        relative_url = "/save"
        label = "events"

        failures = self._doJsonWriteRequest(relative_url, events, label)

        if failures:
            print("Some Events failed to push")
            return failures
        else:
            return True


def get_eventlog(
    eigenserver: EigenServer = None, default_eventlog: Union[str, None] = None
) -> EventLog:
    """
    Connect to Assetmodel of eigenserver. If eigenserver is not provided this will default to the EIGENSERVER environmental variable

    Args:
        eigenserver: An instance of EigenServer() to query

    Returns:
        An object defining a connection to the AssetModel
    """
    if eigenserver is None:
        eigenserver = get_default_server()
    elif isinstance(eigenserver, str):
        eigenserver = EigenServer(eigenserver)

    if default_eventlog is None:
        default_eventlog = "eventlog"
    else:
        default_eventlog = str(default_eventlog)

    return EventLog(
        eigenserver.getEigenServerUrl() + "events" + "/",
        default_eventlog,
        eigenserver.auth,
    )


# Alias for backward compatibility
get_events = get_eventlog
