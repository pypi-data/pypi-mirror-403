"""Helper functions for rich text output"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from urllib.parse import quote

from cmem.cmempy.config import get_cmem_base_uri, get_di_api_endpoint
from cmem.cmempy.workflow.workflow import get_workflow_editor_uri
from cmem.cmempy.workspace import get_task_plugins
from cmem.cmempy.workspace.search import list_items
from humanize import naturalsize, naturaltime

from cmem_cmemc.title_helper import TitleHelper
from cmem_cmemc.utils import get_graphs_as_dict


class StringProcessor(ABC):
    """ABC of a table cell string processor"""

    @abstractmethod
    def process(self, text: str) -> str:
        """Process a single string content and output the processed string."""


class FileSize(StringProcessor):
    """Create a human-readable file size string."""

    def process(self, text: str) -> str:
        """Process a single string content and output the processed string."""
        try:
            return "" if text is None else naturalsize(value=text, gnu=True)
        except ValueError:
            return text


class TimeAgo(StringProcessor):
    """Create a string similar to 'x minutes ago' from a timestamp or iso-formated string."""

    def process(self, text: str) -> str:
        """Process a single string content and output the processed string."""
        if text is None:
            return ""
        try:
            stamp = datetime.fromisoformat(str(text))
            return str(naturaltime(stamp, when=datetime.now(tz=timezone.utc)))
        except (ValueError, TypeError):
            pass
        try:
            text_as_int = int(text)
            stamp = datetime.fromtimestamp(text_as_int / 1000, tz=timezone.utc)
            return str(naturaltime(stamp, when=datetime.now(tz=timezone.utc)))
        except ValueError:
            return text


class GraphLink(StringProcessor):
    """Create a graph link from an IRI cell

    "Visit my [link=https://www.willmcgugan.com]blog[/link]!"
    """

    def __init__(self) -> None:
        self.cmem_base_uri = get_cmem_base_uri()
        self.base = self.cmem_base_uri + "/explore?graph="
        self.graph_labels: dict[str, str] = {}
        for _ in get_graphs_as_dict().values():
            self.graph_labels[_["iri"]] = _["label"]["title"]

    def process(self, text: str) -> str:
        """Process a single string content and output the processed string."""
        link = self.base + quote(text)
        label = self.graph_labels.get(text, None)
        return f"[link={link}]{label}[/link]" if label else text


class QueryLink(StringProcessor):
    """Create a query link from a query IRI cell

    "Visit my [link=https://www.willmcgugan.com]blog[/link]!"
    """

    def __init__(self, catalog_graph: str, queries: dict):
        self.catalog_graph = catalog_graph
        self.queries = queries

    def process(self, text: str) -> str:
        """Process a single string content and output the processed string."""
        # Find the query entry from the queries dict
        query_entry = self.queries.get(text)
        if query_entry:
            # Use the SparqlQuery's get_editor_url method for consistent URL generation
            link = query_entry.get_editor_url(graph=self.catalog_graph)
            label = query_entry.label
            return f"[link={link}]{label}[/link]"
        return text


class ResourceLink(StringProcessor):
    """Create a resource link from an IRI cell

    "Visit my [link=https://www.willmcgugan.com]blog[/link]!"
    """

    def __init__(self, graph_iri: str, title_helper: TitleHelper | None = None):
        self.graph_iri = graph_iri
        self.base = get_cmem_base_uri() + "/explore?graph=" + quote(graph_iri) + "&resource="
        self.title_helper = title_helper if title_helper else TitleHelper()

    def process(self, text: str) -> str:
        """Process a single string content and output the processed string."""
        link = self.base + quote(text)
        label = self.title_helper.get(text)
        return f"[link={link}]{label}[/link]"


class ProjectLink(StringProcessor):
    """Create a project link from a project ID cell

    "Visit my [link=https://www.willmcgugan.com]blog[/link]!"
    """

    def __init__(self, projects: dict):
        self.projects = projects
        self.base = get_di_api_endpoint() + "/workbench/projects/"

    def process(self, text: str) -> str:
        """Process a single string content and output the processed string."""
        project = self.projects.get(text)
        if project:
            link = self.base + text
            label = project["metaData"].get("label", text)
            return f"[link={link}]{label}[/link]"
        return text


class WorkflowLink(StringProcessor):
    """Create a workflow link from a workflow ID cell

    "Visit my [link=https://www.willmcgugan.com]blog[/link]!"
    """

    def __init__(self, workflows: dict):
        self.workflows = workflows
        self.base_uri = get_workflow_editor_uri()

    def process(self, text: str) -> str:
        """Process a single string content and output the processed string."""
        workflow = self.workflows.get(text)
        if workflow:
            project_id, task_id = text.split(":")
            link = self.base_uri.format(project_id, task_id)
            label = workflow["label"]
            return f"[link={link}]{label}[/link]"
        return text


class DatasetTypeLink(StringProcessor):
    """Create a documentation link from a dataset type (pluginId) cell

    Links to the Corporate Memory dataset documentation.
    Example: "json" -> "[link=https://documentation.eccenca.com/latest/build/reference/dataset/json/]JSON[/link]"
    """

    def __init__(
        self, base_url: str = "https://documentation.eccenca.com/latest/build/reference/dataset/"
    ):
        self.base_url = base_url
        self.type_labels: dict[str, str] = {}
        # Dataset types that don't have documentation pages
        self.undocumented_types = {"variableDataset"}
        # Import here to avoid circular imports

        plugins = get_task_plugins()
        for plugin_id, plugin in plugins.items():
            if plugin["taskType"] == "Dataset":
                self.type_labels[plugin_id] = plugin["title"]

    def process(self, text: str) -> str:
        """Process a dataset type and create a documentation link if available."""
        if not text:
            return text

        # Use the title if available, otherwise fall back to the text
        label = self.type_labels.get(text, text)

        # Only create link if this type is not in the undocumented list
        if text not in self.undocumented_types:
            link = f"{self.base_url}{text}/"
            return f"[link={link}]{label}[/link]"

        return label


class DatasetLink(StringProcessor):
    """Create a workspace link from a dataset ID cell

    Links to the Corporate Memory workspace dataset page and displays the dataset label.
    Example: "project:dataset" ->
        "[link=https://cmem.example.com/workspaces/datasets/...]Dataset Label[/link]"
    """

    def __init__(self) -> None:
        self.cmem_base_uri = get_cmem_base_uri()
        self.dataset_urls: dict[str, str] = {}
        self.dataset_labels: dict[str, str] = {}
        # Build a mapping of dataset_id -> URL path and label
        datasets = list_items(item_type="dataset")["results"]
        for dataset in datasets:
            dataset_id = dataset["projectId"] + ":" + dataset["id"]
            url_path = dataset["itemLinks"][0]["path"]
            self.dataset_urls[dataset_id] = url_path
            self.dataset_labels[dataset_id] = dataset["label"]

    def process(self, text: str) -> str:
        """Process a dataset ID and create a workspace link with label if available."""
        if not text:
            return text

        # Check if we have a URL for this dataset ID
        if text in self.dataset_urls:
            full_url = self.cmem_base_uri + self.dataset_urls[text]
            label = self.dataset_labels.get(text, text)
            return f"[link={full_url}]{label}[/link]"

        # If no URL found, return the text as-is
        return text


def process_row(row: list[str], hints: dict[int, StringProcessor]) -> list[str]:
    """Process all cells in a row according to the StringProcessors"""
    processed_row = []
    for column_number, cell in enumerate(row):
        if hints.get(column_number):
            processed_row.append(hints[column_number].process(cell))
        else:
            processed_row.append(cell)
    return processed_row
