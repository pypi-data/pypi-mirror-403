import logging
from collections import namedtuple
from datetime import datetime
from typing import Any, List, Optional

from highlighter.core import GQLBaseModel

from .gql_client import HLClient
from .object_classes import create_object_classes
from .workflow import create_workflow

logger = logging.getLogger(__name__)
IngestionSetup = namedtuple(
    "IngestionSetup", ["data_source_id", "workflow_id", "object_class_uuids", "order_id"]
)


class IngestionBootstrapError(Exception):
    pass


class _Ref(GQLBaseModel):
    id: Optional[str] = None
    uuid: Optional[str] = None
    name: Optional[str] = None


class _IDRef(GQLBaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class _DSResp(GQLBaseModel):
    data_source: Optional[_Ref] = None
    errors: Any = None


class _StepResp(GQLBaseModel):
    workflow_step: Optional[_IDRef] = None
    errors: Any = None


class _OrderResp(GQLBaseModel):
    workflow_order: Optional[_IDRef] = None
    errors: Any = None


def bootstrap_ingestion(client: HLClient, dataset_name: str, class_names: List[str]) -> IngestionSetup:
    # create object classes if they don't exist yet
    oc_map = create_object_classes(client, class_names)
    oc_uuids = [str(v) for v in oc_map.values()]
    if oc_uuids:
        print(f"Synced {len(oc_uuids)} object classes with Highlighter:\n{', '.join(oc_map.keys())}.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_suffix = f"{dataset_name} {timestamp}"

    # create new data source
    ds_name = f"{unique_suffix} Ingestion Source"
    res = client.createDataSource(
        return_type=_DSResp, name=ds_name, sourceType="MANUAL_UPLOAD", contentType="IMAGE"
    )
    if not res.data_source:
        raise IngestionBootstrapError(f"Failed to create data source: {res.errors}.")
    data_source_uuid, data_source_id = res.data_source.uuid, res.data_source.id

    # create new workflow
    wf_name = f"{unique_suffix} Ingestion Workflow"
    wf = create_workflow(client, name=wf_name, object_class_uuids=oc_uuids)
    print(
        f"Created ingestion resources:\n"
        f"    Workflow:\n\tID: {wf.id}\n\tName: {wf.name}\n"
        f"    Data source:\n\tID: {data_source_id}\n\tUUID: {data_source_uuid}."
    )

    # configure a data source step (for seeding), succeeded by a human
    # assessment (annotation) step for our ingestion workflow
    data_source_step = client.createWorkflowStep(
        return_type=_StepResp,
        workflowId=wf.id,
        name="Source Images",
        stepType="data_source",
        dataSourceId=data_source_id,
    )
    if not data_source_step.workflow_step:
        raise IngestionBootstrapError(f'Failed to create "Source Images" step: {data_source_step.errors}.')

    prev = data_source_step.workflow_step.id
    human_assessment_step = client.createWorkflowStep(
        return_type=_StepResp,
        workflowId=wf.id,
        name="Annotate",
        stepType="human_assessment",
        previousStepId=prev,
    )
    if not human_assessment_step.workflow_step:
        raise IngestionBootstrapError(f'Failed to create "Annotate" step: {human_assessment_step.errors}.')

    order_res = client.createWorkflowOrder(
        return_type=_OrderResp,
        workflowId=wf.id,
        name="Ingestion Order",
        state="approved",
        caseMatchingStrategy="none",
    )
    if not order_res.workflow_order:
        raise IngestionBootstrapError(f"Failed to create workflow order: {order_res.errors}.")

    return IngestionSetup(data_source_uuid, int(wf.id), oc_uuids, order_res.workflow_order.id)
