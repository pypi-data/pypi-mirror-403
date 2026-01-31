"""Eigen Ingenuity - Common Menu

This package deals with the Eigen Ingenuity Common Menu API.

To retrieve a CommonMenu instance use getCommonMenu:

  from eigeningenuity.commonmenu import get_common_menu
  from eigeningenuity import EigenServer

  eigenserver = EigenServer(ingenuity-base-url)

  common_menu = get_common_menu(eigenserver)

  assets = common_menu.getRelatedAssetsCommonMenu("System_01")

"""

import json
import pandas as pd
import datetime as dt
from eigeningenuity import EigenServer
from eigeningenuity.util import _do_eigen_json_request
from eigeningenuity.core import get_default_server
from typing import Union
from datetime import datetime
from eigeningenuity.util import force_list


class CommonMenu(object):
    """A common menu instance which talks the Eigen Common Menu API endpoint."""

    def __init__(self, baseurl, auth):
        """This is a constructor. It takes in a URL like http://infra:8080/"""
        self.baseurl = baseurl
        self.auth = auth

    def _doCommonMenuRequest(self, index, params):
        # self._testConnection()
        url = self.baseurl + "commonmenu/asset/" + index + "?"
        return _do_eigen_json_request(url, self.auth, **params)

    def getRelatedAssets(self, node: str, output="json", filepath=None):
        """
        Return all measurement tags directly related to a given asset via the Common Menu API.

        Args:
            node:
            output (Optional): The format in which to return the data. Accepts one of: "raw" - The raw json returned by the API, "json" - A processed version of the json response, "df" - A formatted pandas dataframe object. Defaults to "json".

        Returns:
            A Json containing all nodes with a relation to any node that meets the criteria, and their relationship type.

        Raises:
            KeyError: Raises an exception

        """
        args = {"asset": node}

        response = self._doCommonMenuRequest("relatedAssets", args)
        relatedAssets = response["relatedAssets"]["graphapi"]

        if output == "raw":
            return response

        newAssets = []

        for item in relatedAssets:
            relations = item["relations"]
            for relation in relations:
                newItem = {**item["asset"]}
                newItem["relationName"] = relation["relationName"]
                newItem["direction"] = relation["direction"]
                newAssets.append(newItem)

        if output == "json":
            return newAssets
        if output == "df":
            return pd.json_normalize(newAssets)
        if output == "file":
            if filepath is None:
                filepath = (
                    node
                    + "-RelatedAssets-"
                    + str(dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
                )
            with open(filepath, "w") as f:
                f.write(json.dumps(newAssets, indent=4))

    def getMeasurements(
        self, node: str, source: str = "all", output: str = "json", filepath: str = None
    ):
        """
        Return all measurement tags directly related to a given asset via the Common Menu API.

        Args:
            node: The code (ID) of the node to get related measurements from
            source: The source of the timeseries to return. Accepts one of:
                "all" - All timeseries related to the asset, grouped by source;
                "merged" - All timeseries related to the asset, merged into a single list;
                "{sourceName}" - Timeseries related via the {sourceName}. e.g. "graphapi" or "cognite";
                (default: "all")
            output (Optional): The format in which to return the data. Accepts one of:
                "raw" - The raw json returned by the API;
                "json" - A processed version of the json response;
                "df" - A formatted pandas dataframe object;
                "file" - Downloads the files to a local directory;
                (Defaults to "json")
            filepath (Optional): Name and path to the .json file that will be created/overwritten. If omitted, will create a file in the current directory with a generated name. Has no effect unless output is "file".

        Returns:
            A Json containing all nodes with a relation to any node that meets the criteria, and their relationship type.

        Raises:
            KeyError: Raises an exception

        """
        args = {}
        args["asset"] = node

        response = self._doCommonMenuRequest("timeseries", args)

        source = source.lower()

        if source == "merged":
            timeseries = response["allTimeseries"]
        elif source == "all":
            timeseries = response["timeseries"]
        else:
            timeseries = response["timeseries"][source]

        match output:
            case "raw":
                return response
            case "json":
                return timeseries
            case "df":
                if source == "all":
                    all_data = []
                    for src, items in response["timeseries"].items():
                        for item in items:
                            item["source"] = src
                            all_data.append(item)
                    return pd.DataFrame(all_data)
                else:
                    return pd.DataFrame(timeseries)
            case "file":
                if filepath is None:
                    filepath = (
                        node
                        + "-Measurements-"
                        + str(dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
                    )
                with open(filepath, "w") as f:
                    f.write(json.dumps(timeseries, indent=4))

    def getDrivers(self):
        """
        Return all measurement tags directly related to a given asset via the Common Menu API.

        Args:

        Returns:
            A List of source names that measurements can be retrieved from

        Raises:
            KeyError: Raises an exception

        """
        args = {"asset": ""}

        response = self._doCommonMenuRequest("timeseries", args)

        sources = [driver["name"] for driver in response["drivers"]]

        return sources

    # Alias for getDrivers
    getMeasurementSources = getDrivers

    def getEvents(
        self,
        node: str,
        start: Union[str, int, float, datetime] = "24 hours ago",
        end: Union[str, int, float, datetime] = "now",
        limit: int = 1000,
        output: str = "json",
        filepath: str = None,
    ):
        """
        Return all Events related to nodes via the Common Menu API.

        Args:
            node: The name of the node to query documents for
            start: Timestamp of beginning of time window to search for events, also accepts strings like "30 mins ago"
            end: Timestamp of end of time window to search for events
            output (Optional): The format in which to return the data. Accepts one of:
                "raw" - The raw json returned by the API;
                "json" - A processed version of the json response;
                "df" - A formatted pandas dataframe object;
                "file" - Downloads the files to a local directory;
                (Defaults to "json")
            filepath (Optional): Name and path to the directory created/used for downloaded documents. If omitted, will download files to current directory. Has no effect unless output is "download".

        Returns:
            The set of all documents related to the nodes, the format is dependent on the output parameter. If output is "download", it returns instead the files themselves

        Raises:
            KeyError: Raises an exception

        """
        nodes = force_list(node)
        results = []
        events = []
        for node in nodes:
            args = {"asset": node, "start": start, "end": end, "limit": limit}
            response = self._doCommonMenuRequest("events", args)
            results.append(response)
            events.append(response["events"])

        if events == []:
            return

        if output == "raw":
            return results
        if output == "json":
            return events[0]
        if output == "df":
            return pd.json_normalize(events[0])
        if output == "file":
            if filepath is None:
                filepath = (
                    node
                    + "-RelatedEvents-"
                    + str(dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
                )
            with open(filepath + ".json", "w") as f:
                f.write(json.dumps(events[0], indent=4))

    def getProperties(
        self, node: str, source="all", output="json", filepath: str = None
    ):
        """
        Return all properties of a node via the Assetmodel API

        Args:
            node: The name of the node to return properties of
            source: The source of the properties to return. Accepts one of:
                "all" - All properties assigned to the asset, grouped by source (driver);
                "{sourceName}" - Properties assigned to the asset on the specified {sourceName} (driver). e.g. "graphapi" or "cognite".
                (default: "all")
            output:

        Returns:
            A Json containing all nodes with a relation to any node that meets the criteria, and their relationship type.

        Raises:
            KeyError: Raises an exception

        """

        properties = []
        args = {"asset": node}
        response = self._doCommonMenuRequest("properties", args)

        source = source.lower()

        if source == "all":
            properties = response["properties"]
        else:
            # Get the properties list from the specific source
            source_data = response["properties"].get(source, {})
            properties = source_data.get("properties", {})

        if output == "raw":
            return response
        if output == "json":
            return properties
        if output == "df":
            if source == "all":
                # When source is "all", properties is dict with source keys
                all_data = []
                for src, src_data in properties.items():
                    # Extract the actual properties dict from each source
                    props_dict = src_data.get("properties", {})
                    for key, value in props_dict.items():
                        all_data.append(
                            {"property": key, "value": value, "source": src}
                        )
                return pd.DataFrame(all_data)
            else:
                # When source is specified, properties is already a dict of key-value pairs
                all_data = []
                for key, value in properties.items():
                    all_data.append({"property": key, "value": value})
                return pd.DataFrame(all_data)
        if output == "file":
            if filepath is None:
                filepath = (
                    node
                    + "-Properties-"
                    + str(dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
                )
            with open(filepath, "w") as f:
                f.write(json.dumps(properties, indent=4))

    def getDocuments(
        self, node: str, document_type: str = "all", output="json", filepath: str = None
    ):
        """
        Return all documents of a node via the Common Menu API

        Args:
            node: The name of the node to return documents for
            document_type: The type/grouping of the documents to return. Accepts one of:
                "all" - All documents grouped by document type (default);
                "merged" - All documents in a flat list, ungrouped;
                "{typeName}" - Documents of a specific type only. e.g. "P&ID", "Process Description", etc.;
                (default: "all")
            output (Optional): The format in which to return the data. Accepts one of:
                "raw" - The raw json returned by the API;
                "json" - A processed version of the json response;
                "df" - A formatted pandas dataframe object;
                "file" - Downloads the files to a local directory;
                (Defaults to "json")
            filepath (Optional): Name and path to the .json file that will be created/overwritten. If omitted, will create a file in the current directory with a generated name. Has no effect unless output is "file".

        Returns:
            A Json containing all documents related to the node.

        Raises:
            KeyError: Raises an exception

        """
        args = {"asset": node}

        response = self._doCommonMenuRequest("documents", args)

        documents = response["documents"]

        # Build grouped documents dict
        final_documents = {}
        for type in documents:
            final_documents[type["description"]] = type["documents"]

        # Build flat list of all documents
        alldocs = []
        for type in documents:
            for doc in type["documents"]:
                alldocs.append(doc)

        # Determine which data to return based on source parameter
        source = document_type.lower() if document_type != "all" else document_type

        if source == "merged":
            data_to_return = alldocs
        elif source == "all":
            data_to_return = final_documents
        else:
            # Try to find specific document type (case-insensitive match)
            data_to_return = None
            for type_name, type_docs in final_documents.items():
                if type_name.lower() == source:
                    data_to_return = type_docs
                    break

            # If no match found, return empty list
            if data_to_return is None:
                data_to_return = []

        if output == "raw":
            return response
        if output == "json":
            return data_to_return
        if output == "df":
            if source == "all" or source == "merged":
                return pd.json_normalize(alldocs)
            else:
                return pd.json_normalize(data_to_return)
        if output == "file":
            if filepath is None:
                filepath = (
                    node
                    + "-Documents-"
                    + str(dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
                )


def get_common_menu(eigenserver: EigenServer = None):
    """
    Convenience function to query value from a CommonMenu instance.
    Includes metadata from multiple drivers, and multiple ingenuity databases.
    Only allows querying a single asset at a time. For multiple assets, use the assetmodel module instead, at the expense of data from other sources.

    Args:
        eigenserver: EigenServer instance. If None, will use the default server.

    Returns:
        CommonMenu instance
    """
    if eigenserver is None:
        eigenserver = get_default_server()
    elif isinstance(eigenserver, str):
        eigenserver = EigenServer(eigenserver)

    return CommonMenu(eigenserver.getEigenServerUrl(), eigenserver.auth)
