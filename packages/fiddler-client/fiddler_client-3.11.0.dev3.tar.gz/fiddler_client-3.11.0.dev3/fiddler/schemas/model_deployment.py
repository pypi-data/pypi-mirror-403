from datetime import datetime
from typing import Optional
from uuid import UUID

from fiddler.constants.model_deployment import ArtifactType, DeploymentType
from fiddler.schemas.base import BaseModel
from fiddler.schemas.model import ModelCompactResp
from fiddler.schemas.organization import OrganizationCompactResp
from fiddler.schemas.project import ProjectCompactResp
from fiddler.schemas.user import UserCompactResp


class ModelDeploymentResponse(BaseModel):
    id: UUID
    model: ModelCompactResp
    project: ProjectCompactResp
    organization: OrganizationCompactResp
    artifact_type: str
    deployment_type: str
    active: bool
    image_uri: Optional[str]
    replicas: Optional[int]
    cpu: Optional[int]
    memory: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: UserCompactResp
    updated_by: UserCompactResp


class DeploymentParams(BaseModel):
    """Configuration parameters for deploying a model in the Fiddler platform.

    DeploymentParams defines the deployment configuration for a model, including
    the artifact type, deployment environment, resource allocation, and container
    specifications. These parameters control how the model is packaged, deployed,
    and scaled within the Fiddler infrastructure.

    This class is used when deploying models to specify the runtime environment,
    resource requirements, and deployment strategy that best fits your model's
    needs and performance requirements.

    Attributes:
        artifact_type: Type of model artifact (default: PYTHON_PACKAGE)
        deployment_type: Type of deployment environment (default: BASE_CONTAINER)
        image_uri: Custom container image URI for deployment
        replicas: Number of replica instances to deploy
        cpu: CPU allocation per replica (in cores)
        memory: Memory allocation per replica (in MB)

    Examples:
        Creating basic deployment parameters:

        basic_params = DeploymentParams()

        Creating deployment with custom resources:

        custom_params = DeploymentParams(
            artifact_type=ArtifactType.PYTHON_PACKAGE,
            deployment_type=DeploymentType.BASE_CONTAINER,
            replicas=3,
            cpu=2,
            memory=4096
        )

        Creating deployment with custom container:

        container_params = DeploymentParams(
            artifact_type=ArtifactType.DOCKER_IMAGE,
            deployment_type=DeploymentType.CUSTOM_CONTAINER,
            image_uri="my-registry.com/my-model:v1.0",
            replicas=2,
            cpu=4,
            memory=8192
        )
    """
    artifact_type: str = ArtifactType.PYTHON_PACKAGE
    deployment_type: DeploymentType = DeploymentType.BASE_CONTAINER
    image_uri: Optional[str]
    replicas: Optional[int]
    cpu: Optional[int]
    memory: Optional[int]
