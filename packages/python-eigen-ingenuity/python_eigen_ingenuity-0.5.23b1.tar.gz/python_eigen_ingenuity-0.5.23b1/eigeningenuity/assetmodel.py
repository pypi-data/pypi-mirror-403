"""Eigen Ingenuity - Asset Model

This package deals with the Eigen Ingenuity Asset Model API, by means
of the neo4j plugin endpoint.

To retrieve an AssetObject use getMatchingNodes, or execute a custom cypher query with executeRawQuery

from eigeningenuity.assetmodel import getAssetModel
from eigeningenuity import EigenServer

eigenserver = EigenServer(ingenuity-base-url)

model = getAssetModel(eigenserver)

nodes = model.getMatchingNodes("code","System_")


"""

import requests
import pandas as pd
from eigeningenuity import EigenServer
from eigeningenuity.util import (
    force_list,
    _do_eigen_post_request,
    get_eigenserver,
    EigenException,
)
from eigeningenuity.core import get_default_server
from requests.exceptions import ConnectionError
from urllib.error import URLError
from typing import Union

from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


class AssetModel(object):
    """An assetmodel instance which talks the Eigen Neo4j endpoint."""

    def __init__(self, baseurl, auth, instance="default"):
        """This is a constructor. It takes in a URL like https://demo.eigen.co/ei-applet/"""
        self.baseurl = baseurl
        if instance == "default":
            self.instance = ""
        else:
            self.instance = instance + "/"
        self.eigenserver = get_eigenserver(baseurl)
        self.auth = auth

    def _testConnection(self):
        """Preflight Request to verify connection to ingenuity"""
        try:
            status = requests.get(self.baseurl, verify=False).status_code
        except (URLError, ConnectionError):
            raise ConnectionError(
                "Failed to connect to ingenuity instance at "
                + self.baseurl
                + ". Please check the url is correct and the instance is up."
            )

    def _doNeo4jQueryRequest(self, data):
        # self._testConnection()

        url = f"{self.baseurl}neo4j/{self.instance}query"
        return _do_eigen_post_request(url, data, self.auth)

    def executeRawQuery(self, query: str, output: str = "json"):
        """
        Executes a raw neo4j query against AssetModel via the AssetModel API.

        Args:
            query: A string containing a query in neo4j, for information on neo4j queries see https://neo4j.com/developer/cypher/

        Returns:
            A Json containing the neo4j response to the query.

        Raises:
            KeyError: Raises an exception

        """
        payload = {"q": query}
        resp = self._doNeo4jQueryRequest(payload)

        if output == "raw":
            return resp

        if resp["success"]:
            response = resp["response"]
            data = response["data"]
            if isinstance(data, list) and len(data) >= 1:
                if output == "json":
                    return data
                if output == "df":
                    return pd.json_normalize(data)
            else:
                return response
        else:
            raise EigenException("Query failed: " + str(resp["errors"]))

    def getMeasurements(
        self, nodes: str, prop: str = "code", measurement: str = "", output="json"
    ):
        """
        Return all measurement nodes directly related to a given asset via the AssetModel API. For historian/timeseries metadata, use the commonmenu method instead.

        Args:
            nodes: The value of the property to match
            prop (Optional): The property on to query nodes on. Defaults to code.
            measurement (Optional): Return only tags for a specified measurement type. Defaults to return all tags.

        Returns:
            json:A Json containing all nodes with a relation to any node that meets the criteria, and their relationship type. Structure as follows:
            [
                {"code": "AssetCode",
                "measurementName": "MeasurementType",
                "tag": "TagCode"},
                ...
            ]

        Raises:
            EigenException: Raises an exception if query fails

        """
        nodes_list = force_list(nodes)

        # Build a single efficient query for all nodes
        node_conditions = []
        for node in nodes_list:
            node_conditions.append(f"n.{prop} = '{node}'")

        # Combine all node conditions with OR
        node_match = " OR ".join(node_conditions)

        # Add measurement filter if provided
        measurement_filter = (
            f" AND r.measurementName CONTAINS '{measurement}'" if measurement else ""
        )

        # Single query to get all measurements for all nodes
        if prop != "code":
            code = "n.code as code,"
        else:
            code = ""

        query = f"""
        MATCH (n)-[r:hashistoriantag]->(m) 
        WHERE ({node_match}){measurement_filter}
        RETURN n.{prop} as {prop},{code} r.measurementName as measurementName, m.code as tag
        ORDER BY n.{prop}, r.measurementName
        """

        payload = {"q": query}
        resp = self._doNeo4jQueryRequest(payload)

        # Handle raw output - return full response even if success is false
        if output == "raw":
            return resp

        # Check if query was successful
        if not resp["success"]:
            raise EigenException(f"Query failed: {resp.get('errors', 'Unknown error')}")

        response_data = resp["response"]["data"]

        if output == "json":
            return response_data
        elif output == "df":
            return pd.DataFrame(response_data)
        else:
            raise EigenException(
                f"Unsupported output format: {output}. Use 'json', 'df', or 'raw'."
            )

    def getDocuments(self, nodes: Union[str, list], match=None, output="json"):
        """
        Return all Documents related to nodes via the AssetModel API.

        Args:
            nodes: The name(s) of the node(s) to query documents for
            match (Optional): Filter returned Documents to those with filenames matching a string
            output (Optional): The format in which to return the data. Accepts one of:
                - "raw" - The raw json returned by the API;
                - "json" - A processed version of the json response;
                - "df" - A formatted pandas dataframe object;

        Returns:
            Results: The set of all documents related to the nodes, grouped by node code,
                    the format is dependent on the output parameter.

        Raises:
            EigenException: Raises an exception if query fails

        """
        nodes_list = force_list(nodes)

        # Build a single efficient query for all nodes
        node_conditions = []
        for node in nodes_list:
            node_conditions.append(f"n.code = '{node}'")

        # Combine all node conditions with OR
        node_match = " OR ".join(node_conditions)

        # Single query to get all documents for all nodes, grouped by code
        query = f"""
        MATCH (n)-[r:hasdocument]->(d) 
        WHERE ({node_match})
        RETURN n.code as code, collect(d) as documents
        ORDER BY n.code
        """

        payload = {"q": query}
        resp = self._doNeo4jQueryRequest(payload)

        # Handle raw output - return full response even if success is false
        if output == "raw":
            return resp

        # Check if query was successful
        if not resp["success"]:
            raise EigenException(f"Query failed: {resp.get('errors', 'Unknown error')}")

        response_data = resp["response"]["data"]

        # Process documents and apply filtering
        grouped_documents = {}
        for item in response_data:
            code = item["code"]
            documents = item["documents"]

            # Apply filename/description filter if provided
            if match is not None:
                filtered_docs = []
                for document in documents:
                    if (
                        match in document.get("fileName", "")
                        or match in document.get("description", "")
                        or match in document.get("code", "")
                    ):
                        filtered_docs.append(document)
                grouped_documents[code] = filtered_docs
            else:
                grouped_documents[code] = documents

        if output == "json":
            return grouped_documents
        elif output == "df":
            # For DataFrame, flatten the grouped structure
            flattened = []
            for code, documents in grouped_documents.items():
                for doc in documents:
                    flattened.append({"code": code, **doc})
            return pd.json_normalize(flattened)
        else:
            raise EigenException(
                f"Unsupported output format: {output}. Use 'json', 'df', or 'raw'."
            )

    def getLabels(self, codes: Union[str, list] = None, output: str = "json"):
        """
        List all labels used in an assetmodel instance, or the list of all labels of given nodes

        Args:
            codes (Optional): The value(s) of the code property for the nodes to get labels for.
                            Can be a single string or a list of strings.
            output (Optional): The format in which to return the data. Accepts:
                - "json" - A processed version of the response
                - "raw" - The raw json returned by the API
                - "df" - A formatted pandas dataframe object

        Returns:
            If codes is None: A list of all node labels/types present in the model
            If codes is provided: For single code - list of labels; For multiple codes -
                structured data with nodeCode and labels for each node

        Raises:
            EigenException: Raises an exception if query fails
        """
        if codes is None:
            # Get all labels in the database
            payload = {"q": "CALL db.labels()"}
            resp = self._doNeo4jQueryRequest(payload)

            if output == "raw":
                return resp

            if not resp["success"]:
                raise EigenException(
                    f"Query failed: {resp.get('errors', 'Unknown error')}"
                )

            response_data = resp["response"]["data"]
            labels = [item["label"] for item in response_data]

            if output == "json":
                return labels
            elif output == "df":
                return pd.DataFrame({"label": labels})
            else:
                raise EigenException(
                    f"Unsupported output format: {output}. Use 'json', 'df', or 'raw'."
                )
        else:
            # Get labels for specific nodes
            codes_list = force_list(codes)

            # Build a single efficient query for all codes
            code_conditions = []
            for code in codes_list:
                code_conditions.append(f"n.code = '{code}'")

            # Combine all code conditions with OR
            code_match = " OR ".join(code_conditions)

            # Single query to get labels for all nodes
            query = f"""
            MATCH (n:EI_CURRENT) 
            WHERE ({code_match})
            RETURN n.code as code, labels(n) as labels
            ORDER BY n.code
            """

            payload = {"q": query}
            resp = self._doNeo4jQueryRequest(payload)

            if output == "raw":
                return resp

            if not resp["success"]:
                raise EigenException(
                    f"Query failed: {resp.get('errors', 'Unknown error')}"
                )

            response_data = resp["response"]["data"]

            # Handle single code case for backward compatibility
            if isinstance(codes, str) and len(response_data) > 0:
                if output == "json":
                    return response_data[0]["labels"]
                elif output == "df":
                    return pd.DataFrame({"label": response_data[0]["labels"]})

            # Handle multiple codes case
            if output == "json":
                return response_data
            elif output == "df":
                return pd.json_normalize(response_data)
            else:
                raise EigenException(
                    f"Unsupported output format: {output}. Use 'json', 'df', or 'raw'."
                )

    def getMatchingNodes(
        self,
        criteria: dict,
        match_all: bool = True,
        exact: bool = False,
        output: str = "json",
    ):
        """
        Return all properties of matching nodes via a neo4j query response

        Args:
            criteria: Dictionary of key/value pairs to match on nodes. Special keys:
                - "@labels": Match nodes with specific labels (can be string or list)
                - "@ids": Match nodes with specific IDs (can be string or list)
                - Regular properties: Match on node properties
            match_all (Optional): Whether to match ALL criteria (AND) or ANY criteria (OR). Defaults to True (AND)
            exact (Optional): Whether to use exact matching (=) or partial matching (CONTAINS) for string properties. Defaults to False
            output (Optional): The format in which to return the data. Accepts:
                - "json" - A processed version of the response
                - "raw" - The raw json returned by the API
                - "df" - A formatted pandas dataframe object

        Returns:
            A Json containing all nodes that match the criteria.

        Raises:
            EigenException: Raises an exception if query fails
            ValueError: Raises an exception if criteria is empty or invalid
        """

        if not criteria:
            raise ValueError("Criteria dictionary cannot be empty")

        # Build match conditions
        conditions = []
        match_statement = "MATCH (n)"

        # Handle special @labels key
        if "@labels" in criteria:
            labels = force_list(criteria["@labels"])
            label_conditions = []
            for label in labels:
                # Build label matching - labels are specified in MATCH clause
                if not label_conditions:  # First label
                    match_statement = f"MATCH (n:{label})"
                else:
                    # For multiple labels, we need to check if node has all/any labels
                    label_conditions.append(f"'{label}' IN labels(n)")

            if label_conditions:  # Additional labels beyond the first
                if match_all:
                    conditions.extend(label_conditions)
                else:
                    conditions.append("(" + " OR ".join(label_conditions) + ")")

        # Handle special @ids key
        if "@ids" in criteria:
            ids = force_list(criteria["@ids"])
            id_conditions = []
            for node_id in ids:
                id_conditions.append(f"id(n) = {node_id}")

            if match_all:
                conditions.extend(id_conditions)
            else:
                conditions.append("(" + " OR ".join(id_conditions) + ")")

        # Handle regular properties
        for prop, value in criteria.items():
            if prop.startswith("@"):  # Skip special keys we already handled
                continue

            values = force_list(value)
            prop_conditions = []

            for val in values:
                # Handle different data types appropriately
                if isinstance(val, bool):
                    # Booleans: always use exact match (= operator)
                    prop_conditions.append(f"n.{prop} = {str(val).lower()}")
                elif isinstance(val, (int, float)):
                    # Numbers: always use exact match (= operator)
                    prop_conditions.append(f"n.{prop} = {val}")
                elif isinstance(val, str):
                    # Strings: use exact or CONTAINS based on exact parameter
                    if exact:
                        prop_conditions.append(f"n.{prop} = '{val}'")
                    else:
                        prop_conditions.append(f"n.{prop} CONTAINS '{val}'")
                else:
                    # Other types: convert to string and use exact match
                    prop_conditions.append(f"n.{prop} = '{str(val)}'")

            if match_all:
                conditions.extend(prop_conditions)
            else:
                conditions.append("(" + " OR ".join(prop_conditions) + ")")

        # Combine all conditions
        if conditions:
            if match_all:
                where_clause = " AND ".join(conditions)
            else:
                where_clause = " OR ".join(conditions)
            query = f"{match_statement} WHERE {where_clause} RETURN n ORDER BY n.code"
        else:
            query = f"{match_statement} RETURN n ORDER BY n.code"

        payload = {"q": query}
        resp = self._doNeo4jQueryRequest(payload)

        # Handle raw output - return full response even if success is false
        if output == "raw":
            return resp

        # Check if query was successful
        if not resp["success"]:
            raise EigenException(f"Query failed: {resp.get('errors', 'Unknown error')}")

        response_data = resp = [item["n"] for item in resp["response"]["data"]]

        if output == "json":
            return response_data
        elif output == "df":
            return pd.json_normalize(response_data)
        else:
            raise EigenException(
                f"Unsupported output format: {output}. Use 'json', 'df', or 'raw'."
            )

    def getRelatedAssets(
        self,
        nodes: Union[str, list],
        prop: str = "code",
        exact: bool = False,
        relation: str = None,
        output: str = "json",
    ):
        """
        Return all assets directly related to given assets.

        Args:
            prop: The property on which to match a node
            nodes: The value(s) of the property to match (can be single string or list)
            exact: Whether or not to only apply to assets exactly matching value of node (Defaults to False)
            relation: Specify a required relationship type for returned nodes
            output (Optional): The format in which to return the data. Accepts:
                - "json" - A processed version of the response
                - "raw" - The raw json returned by the API
                - "df" - A formatted pandas dataframe object

        Returns:
            A Json containing all nodes with a relation to any node that meets the criteria, and their relationship type.

        Raises:
            EigenException: Raises an exception if query fails

        """
        nodes_list = force_list(nodes)

        # Build a single efficient query for all nodes
        node_conditions = []
        for node in nodes_list:
            if exact:
                node_conditions.append(f"n.{prop} = '{node}'")
            else:
                node_conditions.append(f"n.{prop} CONTAINS '{node}'")

        # Combine all node conditions with OR
        node_match = " OR ".join(node_conditions)

        # Build relationship filter
        relation_filter = f":{relation}" if relation else ""

        # Single query to get all related assets for all nodes
        query = f"""
        MATCH (n)-[r{relation_filter}]-(m:AssetObject) 
        WHERE ({node_match})
        RETURN n.{prop} as sourceNode, m as relatedAsset, type(r) as relationshipType
        ORDER BY n.{prop}, m.code
        """

        payload = {"q": query}
        resp = self._doNeo4jQueryRequest(payload)

        # Handle raw output - return full response even if success is false
        if output == "raw":
            return resp

        # Check if query was successful
        if not resp["success"]:
            raise EigenException(f"Query failed: {resp.get('errors', 'Unknown error')}")

        response_data = resp["response"]["data"]

        if output == "json":
            return response_data
        elif output == "df":
            return pd.json_normalize(response_data)
        else:
            raise EigenException(
                f"Unsupported output format: {output}. Use 'json', 'df', or 'raw'."
            )


def get_assetmodel(
    eigenserver: EigenServer = None, instance: str = "default"
) -> AssetModel:
    """
    Convenience function for querying data from the Ingenuity Neo4J Assetmodel

    Args:
        (Optional) eigenserver: An instance of EigenServer() to query. Defaults to the EIGENSERVER environmental variable if not provided. Must be provided in one of these ways
        (Optional) instance: The instance name of the AssetModel to connect to, if multiple neo4j instances are available. Defaults to "default".

    Returns:
        An object defining a connection to the AssetModel
    """
    if eigenserver is None:
        eigenserver = get_default_server()
    elif isinstance(eigenserver, str):
        eigenserver = EigenServer(eigenserver)

    return AssetModel(eigenserver.getEigenServerUrl() + "/", eigenserver.auth, instance)


# Aliases
Neo4J = AssetModel  # Alias for AssetModel class
get_neo4j = get_assetmodel  # Alias for get_assetmodel function
