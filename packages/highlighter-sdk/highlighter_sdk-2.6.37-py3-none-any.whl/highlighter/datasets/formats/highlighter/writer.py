import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import pandas as pd
from shapely.geometry.base import BaseGeometry
from tqdm import tqdm

from ....client import (
    Annotation,
    DatumSource,
    Entity,
    HLClient,
    ObjectClass,
    Observation,
)
from ....client import SubmissionType as Submission
from ....client import (
    create_assessment_from_entities,
)
from ....core import (
    OBJECT_CLASS_ATTRIBUTE_UUID,
    PIXEL_LOCATION_ATTRIBUTE_UUID,
    GQLBaseModel,
    LabeledUUID,
)
from ...interfaces import IWriter

logger = logging.getLogger(__name__)


def is_valid_uuid(val):
    if isinstance(val, (LabeledUUID, UUID)):
        return True
    try:
        UUID(val)
        return True
    except (ValueError, TypeError):
        return False


class CreateSubmissionPayload(GQLBaseModel):
    submission: Optional[Submission] = None
    errors: List[str]


class HighlighterAssessmentsWriter(IWriter):
    format_name = "highlighter_assessments"

    def __init__(
        self,
        client: HLClient,
        workflow_id: int,
        object_class_uuid_lookup: Optional[Dict[str, str]] = None,
        user_id: Optional[int] = None,
        task_lookup: Optional[Dict[str, str]] = None,
    ):
        self.client = client
        self.user_id = user_id
        self.workflow_id = workflow_id
        self.task_lookup = task_lookup
        self.object_class_uuid_lookup = object_class_uuid_lookup or self._fetch_class_map()

    def _fetch_class_map(self):
        # fetch server id mapping for labels
        class Workflow(GQLBaseModel):
            object_classes: List[ObjectClass]

        ocs = self.client.workflow(return_type=Workflow, id=self.workflow_id).object_classes
        lookup = {}
        for o in ocs:
            lookup[o.name.lower()] = o.uuid
            lookup[o.name] = o.uuid
            lookup[str(o.id)] = o.uuid
        return lookup

    def _to_uuid(self, name):
        # turn a label name into a server uuid
        if isinstance(name, str):
            return str(
                self.object_class_uuid_lookup.get(name.lower(), self.object_class_uuid_lookup.get(name, name))
            )
        return name

    def _create_assessment_from_file(self, file_id, file_uuid, grp):
        # loop through all entities associated with a single file
        entities = {}
        iterator = [] if grp.empty else grp.groupby("entity_id")
        for eid, ent_df in iterator:
            attrs = ent_df.to_dict("records")
            # TODO: exception handling for entity having multiple geometry attributes
            pixel_loc = next(
                (a for a in attrs if str(a["attribute_id"]) == str(PIXEL_LOCATION_ATTRIBUTE_UUID)), None
            )
            obj_class = next(
                (a for a in attrs if str(a["attribute_id"]) == str(OBJECT_CLASS_ATTRIBUTE_UUID)), None
            )

            # seed UUID with existing entity ID if possible, random otherwise
            entity = Entity(id=UUID(str(eid)) if is_valid_uuid(eid) else uuid4())

            # if this entity had geometry (pixel_loc) and a label (obj_class),
            # we should represent it to Highlighter as an Annotation
            if pixel_loc and obj_class and file_uuid:
                # package a geometric shape and its label for the server
                geom = pixel_loc["value"]
                loc = geom.value if hasattr(geom, "value") and isinstance(geom.value, BaseGeometry) else geom
                anno = Annotation(
                    location=loc,
                    datum_source=DatumSource(confidence=float(pixel_loc["confidence"]), frame_id=0),
                    data_file_id=file_uuid,
                    entity=entity,
                    id=entity.id if is_valid_uuid(eid) else uuid4(),
                )
                # write this entity's class name attribute to an observation,
                # linked back to its data structure in Highlighter (the anno.)
                Observation(
                    attribute_id=OBJECT_CLASS_ATTRIBUTE_UUID,
                    value=self._to_uuid(obj_class["value"]),
                    confidence=float(obj_class["confidence"]),
                    annotation=anno,
                )
                # we should ignore this attribute
                ignored = {id(pixel_loc), id(obj_class)}
                parent_kw = {"annotation": anno}
            else:
                # handle simple data points without shape
                ignored = set()
                parent_kw = {"entity": entity}

            for a in attrs:
                # if we have previously parsed this attribute, or its UUID is
                # invalid
                if id(a) in ignored or not is_valid_uuid(a["attribute_id"]):
                    continue

                val = self._to_uuid(a["value"])
                if hasattr(val, "wkt"):
                    val = val.wkt
                elif isinstance(val, BaseGeometry):
                    val = val.wkt

                # package attribute as observation and inform Highlighter of its
                # structure (entity or annotation) via parent_kw
                Observation(
                    attribute_id=a["attribute_id"],
                    value=val,
                    datum_source=DatumSource(confidence=float(a["confidence"])),
                    **parent_kw,
                )
            entities[entity.id] = entity

        task_id = self.task_lookup.get(str(file_id)) if self.task_lookup else None
        try:
            task_id = UUID(str(task_id)) if task_id else None
        except (ValueError, TypeError):
            task_id = None

        submission = create_assessment_from_entities(
            client=self.client,
            entities=entities,
            data_file_ids=[file_uuid or file_id],
            task_id=task_id,
            workflow_id=self.workflow_id,
            user_id=self.user_id,
            started_at=datetime.now(timezone.utc),
        )
        return file_id, submission.id, submission.hash_signature

    def write(self, dataset):
        # pre-calculate file uuid map
        uuid_map = {}
        if "data_file_uuid" in dataset.data_files_df.columns:
            # ensure string keys for robust lookup
            df = dataset.data_files_df
            uuid_map = dict(zip(df["data_file_id"].astype(str), df["data_file_uuid"]))

        summary = []
        # group this dataset's annotations by file ID
        groups = dataset.annotations_df.groupby("data_file_id") if not dataset.annotations_df.empty else None
        # iterate over every unique file ID in the dataframe
        for fid in tqdm(dataset.data_files_df["data_file_id"].unique()):
            # extract the subset of all annotations associated with this file ID,
            # and upload them
            grp = groups.get_group(fid) if groups and fid in groups.groups else pd.DataFrame()
            file_uuid = uuid_map.get(str(fid))
            summary.append(self._create_assessment_from_file(fid, file_uuid, grp))

        # link server identity back to the local dataset
        id_map = {s[0]: s[1] for s in summary}
        sig_map = {s[0]: s[2] for s in summary}

        dataset.data_files_df["assessment_id"] = dataset.data_files_df["data_file_id"].map(id_map)
        dataset.data_files_df["hash_signature"] = dataset.data_files_df["data_file_id"].map(sig_map)
