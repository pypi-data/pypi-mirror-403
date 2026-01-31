"""Title helper functions."""

import json
from typing import ClassVar

from cmem.cmempy.api import get_json
from cmem.cmempy.config import get_dp_api_endpoint
from cmem.cmempy.workspace import get_task_plugins
from cmem.cmempy.workspace.projects.project import get_projects


class TitleHelper:
    """Title helper class."""

    fetched_labels: dict[str, dict]

    def __init__(self) -> None:
        self.fetched_labels = {}
        self.endpoint = f"{get_dp_api_endpoint()}/api/explore/titles"

    def get(self, iri: str | list[str]) -> str | dict[str, str]:
        """Get the title of an IRI (or list of IRI)."""
        output = {}
        iris = [iri] if isinstance(iri, str) else list(set(iri))

        iris_to_fetch = []
        for _ in iris:
            if _ in self.fetched_labels:
                output[_] = self.fetched_labels[_]["title"]
            else:
                iris_to_fetch.append(_)

        if len(iris_to_fetch) > 0:
            titles: dict = get_json(
                self.endpoint,
                method="POST",
                data=json.dumps(iris_to_fetch),
                headers={"Content-type": "application/json"},
            )
            for title in titles.values():
                self.fetched_labels[title["iri"]] = title
                output[title["iri"]] = title["title"]

        return output[iri] if isinstance(iri, str) else output


class ProjectTitleHelper(TitleHelper):
    """Title helper for project IDs with class-level caching."""

    _labels_cache: ClassVar[dict[str, str]] = {}
    _cache_initialized: ClassVar[bool] = False

    def get(self, project_id: str | list[str]) -> str | dict[str, str]:
        """Get the label of a project (or list of projects)."""
        # Fetch all project labels once at class level
        if not ProjectTitleHelper._cache_initialized:
            projects = get_projects()
            for project in projects:
                ProjectTitleHelper._labels_cache[project["name"]] = project["metaData"].get(
                    "label", ""
                )
            ProjectTitleHelper._cache_initialized = True

        # Build and return output
        if isinstance(project_id, str):
            return ProjectTitleHelper._labels_cache.get(project_id, "")
        return {pid: ProjectTitleHelper._labels_cache.get(pid, "") for pid in project_id}


class DatasetTypeTitleHelper(TitleHelper):
    """Title helper for dataset types with class-level caching."""

    _labels_cache: ClassVar[dict[str, str]] = {}
    _cache_initialized: ClassVar[bool] = False

    def get(self, plugin_id: str | list[str]) -> str | dict[str, str]:
        """Get the description of a dataset type (or list of types)."""
        # Fetch all plugin descriptions once at class level
        if not DatasetTypeTitleHelper._cache_initialized:
            plugins = get_task_plugins()
            for pid, plugin in plugins.items():
                if plugin["taskType"] == "Dataset":
                    title = plugin["title"]
                    description = plugin["description"].partition("\n")[0]
                    DatasetTypeTitleHelper._labels_cache[pid] = f"{title}: {description}"
            DatasetTypeTitleHelper._cache_initialized = True

        # Build and return output
        if isinstance(plugin_id, str):
            return DatasetTypeTitleHelper._labels_cache.get(plugin_id, plugin_id)
        return {pid: DatasetTypeTitleHelper._labels_cache.get(pid, pid) for pid in plugin_id}
