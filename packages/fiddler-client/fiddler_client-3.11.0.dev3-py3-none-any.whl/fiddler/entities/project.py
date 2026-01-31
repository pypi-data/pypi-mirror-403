"""
Project entity for organizing and managing ML models in Fiddler.

The Project class represents a logical container for organizing related machine learning
models, datasets, and monitoring configurations. Projects provide isolation, access control,
and organizational structure for ML monitoring workflows.

Key Concepts:
    - **Organization**: Projects group related models and resources together
    - **Isolation**: Each project maintains separate namespaces for models and data
    - **Access Control**: Projects can have different permissions and access levels
    - **Lifecycle Management**: Projects coordinate the lifecycle of contained resources

Common Workflow:
    1. Create or retrieve a project for your ML use case
    2. Add models to the project using Model.create() or Model.from_data()
    3. Configure monitoring, alerts, and baselines for project models
    4. Manage project-level settings and access permissions

Example:
    # Create a new project
    project = Project(name="fraud_detection").create()

    # Add models to the project
    model = Model.from_data(
        source=training_data,
        name="fraud_model_v1",
        project_id=project.id
    )
    model.create()

    # List all models in the project
    for model in project.models:
        print(f"Model: {model.name}")

Note:
    Project names must be unique within an organization and follow slug-like naming
    conventions (lowercase, hyphens, underscores allowed). Projects cannot be renamed
    after creation, but can be deleted if no longer needed.
"""
from __future__ import annotations

import logging
import typing
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import UUID

from fiddler.decorators import handle_api_error
from fiddler.entities.base import BaseEntity
from fiddler.exceptions import NotFound
from fiddler.schemas.filter_query import OperatorType, QueryCondition, QueryRule
from fiddler.schemas.project import ProjectResp
from fiddler.utils.decorators import check_version
from fiddler.utils.helpers import raise_not_found

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from fiddler.entities.model import ModelCompact


class Project(BaseEntity):
    """Represents a project container for organizing ML models and resources.

    A Project is the top-level organizational unit in Fiddler that groups related
    machine learning models, datasets, and monitoring configurations. Projects provide
    logical separation, access control, and resource management for ML monitoring workflows.

    Key Features:
        - **Model Organization**: Container for related ML models and their versions
        - **Resource Isolation**: Separate namespaces prevent naming conflicts
        - **Access Management**: Project-level permissions and access control
        - **Monitoring Coordination**: Centralized monitoring and alerting configuration
        - **Lifecycle Management**: Coordinated creation, updates, and deletion of resources

    Project Lifecycle:
        1. **Creation**: Create project with unique name within organization
        2. **Model Addition**: Add models using Model.create() or Model.from_data()
        3. **Configuration**: Set up monitoring, alerts, and baseline comparisons
        4. **Operations**: Publish data, monitor performance, manage alerts
        5. **Maintenance**: Update configurations, add new model versions
        6. **Cleanup**: Delete project when no longer needed (removes all contained resources)

    Attributes:
        name (str): Project name, must be unique within the organization.
                   Should follow slug-like naming (lowercase, hyphens, underscores).
        id (UUID, optional): Unique project identifier, assigned by server on creation.
        created_at (datetime, optional): Project creation timestamp.
        updated_at (datetime, optional): Last modification timestamp.

    Example:
        # Create a new project for fraud detection models
        project = Project(name="fraud-detection-2024")
        project = project.create()
        print(f"Created project: {project.name} (ID: {project.id})")

        # Add a model to the project
        model = Model.from_data(
            source=training_df,
            name="xgboost_v1",
            project_id=project.id,
            task=ModelTask.BINARY_CLASSIFICATION
        )
        model.create()

        # List all models in the project
        models = list(project.models)
        print(f"Project contains {len(models)} models")

        # Access project models
        for model_compact in project.models:
            full_model = model_compact.fetch()
            print(f"Model: {full_model.name} (Task: {full_model.task})")

    Note:
        Projects are permanent containers - once created, the name cannot be changed.
        Deleting a project removes all contained models, datasets, and configurations.
        Consider the organizational structure carefully before creating projects.
    """
    def __init__(self, name: str) -> None:
        """Initialize a Project instance.

        Creates a new Project object with the specified name. The project is not
        created on the Fiddler platform until .create() is called.

        Args:
            name: Project name, must be unique within the organization.
                 Should follow slug-like naming conventions:
                 - Use lowercase letters, numbers, hyphens, and underscores
                 - Start with a letter or number
                 - Be descriptive of the project's purpose
                 - Examples: "fraud-detection", "churn_prediction_2024", "nlp-models"

        Example:
            # Create project instance for fraud detection
            project = Project(name="fraud-detection-prod")

            # Create project instance for experimentation
            experiment_project = Project(name="ml-experiments-q1-2024")

            # Create on platform
            created_project = project.create()
            print(f"Project created with ID: {created_project.id}")

        Note:
            The project exists only locally until .create() is called. Project names
            cannot be changed after creation, so choose descriptive, permanent names.
            Consider your organization's naming conventions and project structure.
        """
        self.name = name

        self.id: UUID | None = None
        self.created_at: datetime | None = None
        self.updated_at: datetime | None = None

        # Deserialized response object
        self._resp: ProjectResp | None = None

    @staticmethod
    def _get_url(id_: UUID | str | None = None) -> str:
        """Get project resource/item url"""
        url = '/v3/projects'
        return url if not id_ else f'{url}/{id_}'

    @classmethod
    def _from_dict(cls, data: dict) -> Project:
        """Build entity object from the given dictionary"""

        # Deserialize the response
        resp_obj = ProjectResp(**data)

        # Initialize
        instance = cls(
            name=resp_obj.name,
        )

        # Add remaining fields
        fields = ['id', 'created_at', 'updated_at']
        for field in fields:
            setattr(instance, field, getattr(resp_obj, field, None))

        instance._resp = resp_obj
        return instance

    def _refresh(self, data: dict) -> None:
        """Refresh the fields of this instance from the given response dictionary"""
        # Deserialize the response
        resp_obj = ProjectResp(**data)

        fields = [
            'id',
            'name',
            'created_at',
            'updated_at',
        ]
        for field in fields:
            setattr(self, field, getattr(resp_obj, field, None))

        self._resp = resp_obj

    @classmethod
    @handle_api_error
    def get(cls, id_: UUID | str) -> Project:
        """Retrieve a project by its unique identifier.

        Fetches a project from the Fiddler platform using its UUID. This is the most
        direct way to retrieve a project when you know its ID.

        Args:
            id_: The unique identifier (UUID) of the project to retrieve.
                Can be provided as a UUID object or string representation.

        Returns:
            :class:`~fiddler.entities.Project`: The project instance with all metadata and configuration.

        Raises:
            NotFound: If no project exists with the specified ID.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Get project by UUID
            project = Project.get(id_="550e8400-e29b-41d4-a716-446655440000")
            print(f"Retrieved project: {project.name}")
            print(f"Created: {project.created_at}")

            # Access project models
            model_count = len(list(project.models))
            print(f"Project contains {model_count} models")

        Note:
            This method makes an API call to fetch the latest project state from the server.
            The returned project instance reflects the current state in Fiddler.
        """
        response = cls._client().get(url=cls._get_url(id_))
        return cls._from_response(response=response)

    @classmethod
    @handle_api_error
    def from_name(cls, name: str) -> Project:
        """Retrieve a project by name.

        Finds and returns a project using its name within the organization. This is useful
        when you know the project name but not its UUID. Project names are unique within
        an organization, making this a reliable lookup method.

        Args:
            name: The name of the project to retrieve. Project names are unique
                 within an organization and are case-sensitive.

        Returns:
            :class:`~fiddler.entities.Project`: The project instance matching the specified name.

        Raises:
            NotFound: If no project exists with the specified name in the organization.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Get project by name
            project = Project.from_name(name="fraud-detection")
            print(f"Found project: {project.name} (ID: {project.id})")
            print(f"Created: {project.created_at}")

            # Use project to list models
            for model in project.models:
                print(f"Model: {model.name} v{model.version}")

            # Get project for specific environment
            prod_project = Project.from_name(name="fraud-detection-prod")
            staging_project = Project.from_name(name="fraud-detection-staging")

        Note:
            Project names are case-sensitive and must match exactly. Use this method
            when you have a known project name from configuration or user input.
        """
        _filter = QueryCondition(
            rules=[QueryRule(field='name', operator=OperatorType.EQUAL, value=name)]
        )

        response = cls._client().get(
            url=cls._get_url(), params={'filter': _filter.json()}
        )
        if response.json()['data']['total'] == 0:
            raise_not_found('Project not found for the given identifier')

        return cls._from_dict(data=response.json()['data']['items'][0])

    @classmethod
    @handle_api_error
    def list(cls) -> Iterator[Project]:
        """List all projects in the organization.

        Retrieves all projects that the current user has access to within the organization.
        Returns an iterator for memory efficiency when dealing with many projects.

        Yields:
            :class:`~fiddler.entities.Project`: Project instances for all accessible projects.

        Raises:
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # List all projects
            for project in Project.list():
                print(f"Project: {project.name}")
                print(f"  ID: {project.id}")
                print(f"  Created: {project.created_at}")
                print(f"  Models: {len(list(project.models))}")

            # Convert to list for counting and filtering
            projects = list(Project.list())
            print(f"Total accessible projects: {len(projects)}")

            # Find projects by name pattern
            prod_projects = [
                p for p in Project.list()
                if "prod" in p.name.lower()
            ]
            print(f"Production projects: {len(prod_projects)}")

            # Get project summaries
            for project in Project.list():
                model_count = len(list(project.models))
                print(f"{project.name}: {model_count} models")

        Note:
            This method returns an iterator for memory efficiency. Convert to a list
            with list(Project.list()) if you need to iterate multiple times or get
            the total count. The iterator fetches projects lazily from the API.
        """
        for project in cls._paginate(url=cls._get_url()):
            yield cls._from_dict(data=project)

    @handle_api_error
    def create(self) -> Project:
        """Create the project on the Fiddler platform.

        Persists this project instance to the Fiddler platform, making it available
        for adding models, configuring monitoring, and other operations. The project
        must have a unique name within the organization.

        Returns:
            :class:`~fiddler.entities.Project`: This project instance, updated with server-assigned fields like
                  ID, creation timestamp, and other metadata.

        Raises:
            Conflict: If a project with the same name already exists in the organization.
            ValidationError: If the project configuration is invalid (e.g., invalid name format).
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Create a new project
            project = Project(name="customer-churn-analysis")
            created_project = project.create()
            print(f"Created project with ID: {created_project.id}")
            print(f"Created at: {created_project.created_at}")

            # Project is now available for adding models
            assert created_project.id is not None

            # Add a model to the newly created project
            model = Model.from_data(
                source=training_data,
                name="churn_model_v1",
                project_id=created_project.id
            )
            model.create()

        Note:
            After successful creation, the project instance is updated in-place with
            server-assigned metadata. The same instance can be used for subsequent
            operations without needing to fetch it again.
        """
        response = self._client().post(
            url=self._get_url(),
            # Simple object, stdlib JSON encoding good enough.
            json={'name': self.name},
        )
        self._refresh_from_response(response=response)
        return self

    @classmethod
    @handle_api_error
    def get_or_create(cls, name: str) -> Project:
        """Get an existing project by name or create a new one if it doesn't exist.

        This is a convenience method that attempts to retrieve a project by name,
        and if not found, creates a new project with that name. Useful for idempotent
        project setup in automation scripts and deployment pipelines.

        Args:
            name: The name of the project to retrieve or create. Must follow
                 project naming conventions (slug-like format).

        Returns:
            :class:`~fiddler.entities.Project`: Either the existing project with the specified name,
                  or a newly created project if none existed.

        Raises:
            ValidationError: If the project name format is invalid.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Safe project setup - get existing or create new
            project = Project.get_or_create(name="fraud-detection-prod")
            print(f"Using project: {project.name} (ID: {project.id})")

            # Idempotent setup in deployment scripts
            project = Project.get_or_create(name="ml-pipeline-staging")

            # Add models safely - project guaranteed to exist
            model = Model.from_data(
                source=data,
                name="model_v1",
                project_id=project.id
            )
            model.create()

            # Use in configuration management
            environments = ["dev", "staging", "prod"]
            projects = {}
            for env in environments:
                projects[env] = Project.get_or_create(name=f"fraud-detection-{env}")

        Note:
            This method is idempotent - calling it multiple times with the same name
            will return the same project. It logs when creating a new project for
            visibility in automation scenarios.
        """
        try:
            return cls.from_name(name=name)
        except NotFound:
            logger.info('Project not found, creating a new one - `%s`', name)
            return Project(name=name).create()

    @check_version(version_expr='>=25.2.0')
    @handle_api_error
    def delete(self) -> None:
        """Delete the project and all its contained resources.

        Permanently removes the project from the Fiddler platform, including all
        associated models, datasets, baselines, alerts, and monitoring configurations.
        This operation cannot be undone.

        Raises:
            NotFound: If the project doesn't exist or has already been deleted.
            ApiError: If there's an error communicating with the Fiddler API.
            PermissionError: If the user doesn't have permission to delete the project.

        Warning:
            This operation is irreversible and will delete ALL resources associated
            with the project, including:
            - All models and their versions
            - All datasets and published data
            - All baselines and monitoring configurations
            - All alert rules and notification settings
            - All access permissions and project settings

        Example:
            # Delete a test or temporary project
            test_project = Project.from_name(name="temp-experiment")
            test_project.delete()
            print(f"Deleted project: {test_project.name}")

            # Safe deletion with confirmation
            project = Project.from_name(name="old-project")
            model_count = len(list(project.models))
            if model_count == 0:
                project.delete()
                print("Empty project deleted")
            else:
                print(f"Project has {model_count} models - deletion cancelled")

            # Cleanup projects by pattern
            for project in Project.list():
                if project.name.startswith("temp-"):
                    print(f"Deleting temporary project: {project.name}")
                    project.delete()

        Note:
            Requires Fiddler platform version 25.2.0 or higher. Consider exporting
            important data or configurations before deletion. There is no recovery
            mechanism once a project is deleted.
        """
        assert self.id is not None

        self._client().delete(url=self._get_url(id_=self.id))

    @property
    def models(self) -> Iterator[ModelCompact]:
        """Fetch all the models of this project.

        Yields:
            :class:`~fiddler.entities.ModelCompact`: Lightweight model objects for this project.
        """
        from fiddler.entities.model import (  # pylint: disable=import-outside-toplevel
            Model,
        )

        assert self.id is not None

        yield from Model.list(project_id=self.id)


@dataclass
class ProjectCompact:
    """Lightweight project representation for listing and basic operations.

    A minimal project object containing only essential identifiers. Used by
    various listing operations to efficiently return project information without
    fetching full project details and associated resources.

    This class provides a memory-efficient way to work with project references
    when you don't need the full project functionality but want to access
    basic information or fetch the complete project when needed.

    Attributes:
        id (UUID): Unique project identifier
        name (str): Project name within the organization

    Example:
        # From project references in other entities
        model = Model.get(id_="model-uuid")
        project_compact = model.project  # Returns ProjectCompact

        # Access basic info
        print(f"Project: {project_compact.name}")
        print(f"ID: {project_compact.id}")

        # Fetch full details when needed
        full_project = project_compact.fetch()
        print(f"Created: {full_project.created_at}")
        print(f"Models: {len(list(full_project.models))}")

    Note:
        ProjectCompact objects are typically returned by other entities that
        reference projects. Use .fetch() to get the complete Project instance
        when you need full functionality like listing models or project operations.
    """
    id: UUID
    name: str

    def fetch(self) -> Project:
        """Fetch project instance.

        Returns:
            :class:`~fiddler.entities.Project`: Complete project instance with all details.
        """
        return Project.get(id_=self.id)


class ProjectCompactMixin:
    @property
    def project(self) -> ProjectCompact:
        """Get the project reference for this entity.

        Returns a lightweight ProjectCompact object containing the project
        information associated with this entity. Use .fetch() on the returned
        object to get the complete Project instance.

        Returns:
            :class:`~fiddler.entities.ProjectCompact`: Lightweight project reference with id and name.

        Raises:
            AttributeError: If this property is accessed on an object not generated
                          from an API response, or if the response doesn't contain project information.

        Example:
            # Get project reference from a model
            model = Model.get(id_="model-uuid")
            project_ref = model.project
            print(f"Model belongs to project: {project_ref.name}")

            # Fetch complete project details
            full_project = project_ref.fetch()
            print(f"Project created: {full_project.created_at}")

        Note:
            This property is only available on objects that were fetched from the
            Fiddler API and contain project reference information in their response.
        """
        response = getattr(self, '_resp', None)
        if not response or not hasattr(response, 'project'):
            raise AttributeError(
                'This property is available only for objects generated from API '
                'response.'
            )

        return ProjectCompact(id=response.project.id, name=response.project.name)
