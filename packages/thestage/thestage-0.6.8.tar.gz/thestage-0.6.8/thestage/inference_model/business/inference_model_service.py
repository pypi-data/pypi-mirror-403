import time
from datetime import datetime
from typing import Optional, List

import boto3
import typer

from thestage.config.business.config_provider import ConfigProvider
from thestage.helpers.error_handler import error_handler
from thestage.i18n.translation import __
from thestage.inference_model.business.mapper.inference_model_mapper import InferenceModelMapper
from thestage.inference_model.communication.inference_model_api_client import InferenceModelApiClient
from thestage.inference_model.dto.deploy_inference_model_to_instance_response import \
    DeployInferenceModelToInstanceResponse
from thestage.inference_model.dto.deploy_inference_model_to_sagemaker_response import \
    DeployInferenceModelToSagemakerResponse
from thestage.inference_model.dto.enum.inference_model_status import InferenceModelStatus
from thestage.inference_model.dto.inference_model import InferenceModel
from thestage.inference_model.dto.inference_model_entity import InferenceModelEntity
from thestage.project.business.project_service import ProjectService
from thestage.project.dto.project_config import ProjectConfig
from thestage.services.abstract_service import AbstractService
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList


class InferenceModelService(AbstractService):
    def __init__(
            self,
            inference_model_api_client: InferenceModelApiClient,
            config_provider: ConfigProvider,
            project_service: ProjectService,
    ):
        self.__inference_model_api_client = inference_model_api_client
        self.__config_provider = config_provider
        self.__project_service = project_service


    @error_handler()
    def get_project_inference_simulator_model_list(
            self,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            statuses: List[str],
            row: int = 5,
            page: int = 1,
    ) -> PaginatedEntityList[InferenceModel]:
        data: Optional[
            PaginatedEntityList[InferenceModel]] = self.__inference_model_api_client.get_inference_simulator_model_list_for_project(
            statuses=statuses,
            project_public_id=project_public_id,
            project_slug=project_slug,
            page=page,
            limit=row,
        )

        return data

    @error_handler()
    def project_deploy_inference_simulator_model_to_instance(
            self,
            model_public_id: Optional[str] = None,
            model_slug: Optional[str] = None,
            rented_instance_public_id: Optional[str] = None,
            rented_instance_slug: Optional[str] = None,
            self_hosted_instance_public_id: Optional[str] = None,
            self_hosted_instance_slug: Optional[str] = None,
    ) -> str:
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__project_service.get_fixed_project_config()
        if not project_config:
            typer.echo(
                __("No project found at the path: %path%. Please initialize or clone a project first. Or provide path to project using --working-directory option.",
                   {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        instance_args_count = sum(v is not None for v in
                                  [rented_instance_public_id, rented_instance_slug, self_hosted_instance_public_id,
                                   self_hosted_instance_slug])
        if instance_args_count != 1:
            typer.echo("Please provide a single instance (rented or self-hosted) identifier - name or ID.")
            raise typer.Exit(1)

        model_args_count = sum(v is not None for v in [model_public_id, model_slug])
        if model_args_count != 1:
            typer.echo("Please provide a single model identifier - name or ID.")
            raise typer.Exit(1)

        typer.echo(f"Creating inference simulator")
        deploy_model_to_instance_response: DeployInferenceModelToInstanceResponse = self.__inference_model_api_client.deploy_inference_model_to_instance(
            model_public_id=model_public_id,
            model_slug=model_slug,
            rented_instance_public_id=rented_instance_public_id,
            rented_instance_slug=rented_instance_slug,
            self_hosted_instance_public_id=self_hosted_instance_public_id,
            self_hosted_instance_slug=self_hosted_instance_slug,
        )
        if deploy_model_to_instance_response:
            if deploy_model_to_instance_response.message:
                typer.echo(deploy_model_to_instance_response.message)
            if deploy_model_to_instance_response.is_success:
                typer.echo("Inference simulator has been scheduled to run successfully.")
            else:
                typer.echo(__(
                    'Failed to start inference simulator: %server_massage%',
                    {'server_massage': deploy_model_to_instance_response.message or ""}
                ))
                raise typer.Exit(1)
        else:
            typer.echo(__("Failed to start inference simulator"))
            raise typer.Exit(1)

        return deploy_model_to_instance_response.inferenceSimulatorPublicId


    @error_handler()
    def project_deploy_inference_simulator_model_to_sagemaker(
            self,
            model_public_id: Optional[str] = None,
            model_slug: Optional[str] = None,
            arn: Optional[str] = None,
            instance_type: Optional[str] = None,
            initial_variant_weight: Optional[float] = 1.0,
            initial_instance_count: Optional[int] = None,
    ) -> None:
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__project_service.get_fixed_project_config()
        if not project_config:
            typer.echo(
                __("No project found at the path: %path%. Please initialize or clone a project first. Or provide path to project using --working-directory option.",
                   {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        if not instance_type:
            typer.echo(__("Error: Instance type is required."))
            raise typer.Exit(1)

        if not initial_instance_count:
            typer.echo(__("Error: Initial instance count is required."))
            raise typer.Exit(1)

        if not arn:
            typer.echo(__("Error: ARN is required."))
            raise typer.Exit(1)

        project_config: ProjectConfig = self.__config_provider.read_project_config()
        if not project_config:
            typer.echo(__("No project found at the path: %path%. Please initialize or clone a project first.",
                          {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        deploy_model_to_sagemaker_response: DeployInferenceModelToSagemakerResponse = self.__inference_model_api_client.deploy_inference_model_to_sagemaker(
            model_public_id=model_public_id,
            model_slug=model_slug,
            arn=arn,
        )

        if not deploy_model_to_sagemaker_response.is_success:
            typer.echo(__(
                'Model deployment preparation failed: %server_massage%',
                {'server_massage': deploy_model_to_sagemaker_response.message or ""}
            ))
            raise typer.Exit(1)

        model_id = deploy_model_to_sagemaker_response.modelId
        image_uri = deploy_model_to_sagemaker_response.ecrImageUrl
        model_uri = deploy_model_to_sagemaker_response.s3ArtifactsUrl
        region = "us-east-1"
        sm_client = boto3.client('sagemaker', region_name=region)

        try:
            container = {
                "Image": image_uri,
                "ModelDataUrl": model_uri,
                "Environment": {
                    "SAGEMAKER_TRITON_DEFAULT_MODEL_NAME": model_id,
                    "THESTAGE_API_URL": config.main.thestage_api_url,
                    "THESTAGE_AUTH_TOKEN": config.main.thestage_auth_token
                },
            }

            sm_model_name = f"{model_slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            create_model_response = sm_client.create_model(
                ModelName=sm_model_name,
                ExecutionRoleArn=arn,
                PrimaryContainer=container,
            )
            typer.echo(f"Model created successfully. Model ARN: {create_model_response['ModelArn']}")

            endpoint_config_name = f"{model_slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            create_endpoint_config_response = sm_client.create_endpoint_config(
                EndpointConfigName=endpoint_config_name,
                ProductionVariants=[
                    {
                        "InstanceType": instance_type,
                        "InitialVariantWeight": initial_variant_weight,
                        "InitialInstanceCount": initial_instance_count,
                        "ModelName": sm_model_name,
                        "VariantName": "AllTraffic",
                    }
                ],
            )
            typer.echo(
                f"Endpoint configuration created successfully. Endpoint Config ARN: {create_endpoint_config_response['EndpointConfigArn']}")

            endpoint_name = f"{model_slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            create_endpoint_response = sm_client.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_config_name,
            )
            typer.echo(f"Endpoint created successfully. Endpoint ARN: {create_endpoint_response['EndpointArn']}")

            typer.echo("Waiting for the endpoint to become active...")
            while True:
                resp = sm_client.describe_endpoint(EndpointName=endpoint_name)
                status = resp["EndpointStatus"]
                typer.echo(f"Status: {status}")
                if status == "InService":
                    break
                elif status == "Failed":
                    typer.echo(f"Endpoint creation failed. Reason: {resp.get('FailureReason', 'Unknown')}")
                    raise typer.Exit(1)
                time.sleep(60)

            typer.echo(f"Endpoint is ready. ARN: {resp['EndpointArn']} Status: {status}")

        except Exception as e:
            typer.echo(__("Failed to deploy the inference simulator model to SageMaker: %error%", {"error": str(e)}))
            raise typer.Exit(1)


    @error_handler()
    def print_inference_simulator_model_list(self, project_public_id, project_slug, statuses, row, page):
        if not project_public_id and not project_slug:
            project_config: ProjectConfig = self.__config_provider.read_project_config()
            if not project_config:
                typer.echo(__("Provide the project unique ID or run this command from within an initialized project directory"))
                raise typer.Exit(1)
            project_public_id = project_config.public_id

        inference_simulator_model_status_map = self.__inference_model_api_client.get_inference_simulator_model_business_status_map()

        if not statuses:
            statuses = ({key: inference_simulator_model_status_map[key] for key in [
                InferenceModelStatus.SCHEDULED,
                InferenceModelStatus.PROCESSING,
                InferenceModelStatus.PUSH_SUCCEED,
            ]}).values()

        if "all" in statuses:
            statuses = inference_simulator_model_status_map.values()

        for input_status_item in statuses:
            if input_status_item not in inference_simulator_model_status_map.values():
                typer.echo(__("'%invalid_status%' is not one of %valid_statuses%", {
                    'invalid_status': input_status_item,
                    'valid_statuses': str(list(inference_simulator_model_status_map.values()))
                }))
                raise typer.Exit(1)

        typer.echo(__(
            "Listing inference simulator models with the following statuses: %statuses%, to view all inference simulator models, use --status all",
            placeholders={
                'statuses': ', '.join([status_item for status_item in statuses])
            }))

        backend_statuses: List[str] = [key for key, value in inference_simulator_model_status_map.items() if value in statuses]

        self.print(
            func_get_data=self.get_project_inference_simulator_model_list,
            func_special_params={
                'project_public_id': project_public_id,
                'project_slug': project_slug,
                'statuses': backend_statuses,
            },
            mapper=InferenceModelMapper(),
            headers=list(map(lambda x: x.alias, InferenceModelEntity.model_fields.values())),
            row=row,
            page=page,
            max_col_width=[100, 100, 100, 100, 25],
            show_index="never",
        )