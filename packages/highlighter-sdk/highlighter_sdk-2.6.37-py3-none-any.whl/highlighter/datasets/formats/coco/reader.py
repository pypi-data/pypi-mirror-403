import json
import logging
from pathlib import Path
from typing import List, Tuple, Union
from uuid import uuid4

from PIL import Image

from highlighter.core.geometry import (
    multipolygon_from_coords,
    polygon_from_left_top_width_height_coords,
)

from ....client import PixelLocationAttributeValue
from ....core import OBJECT_CLASS_ATTRIBUTE_UUID
from ...base_models import AttributeRecord, ImageRecord
from ...common import SUPPORTED_IMAGE_EXTENSIONS
from ...interfaces import IReader
from .common import CocoKeys

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]


class CocoReader(IReader):
    """
    Parses a COCO dataset, returning a comprehensive list of its images and attributes.

    This reader treats the local filesystem as the source of truth and handles:
    - Verification of image existence and integrity, automatically skipping missing or corrupt files.
    - Extraction of true image dimensions from disk to supervise potentially inaccurate JSON metadata.
    - Graceful recovery from a malformed geometry or an invalid category identifier.

    Requirements:
    - A valid COCO JSON annotation file.
    - A directory containing the corresponding images.
    """

    format_name = "coco"

    def __init__(
        self,
        json_path: PathLike,
        image_dir: PathLike,
        bbox_only: bool = False,
        fix_invalid_polygons: bool = False,
    ):
        self.json_path = Path(json_path)
        self.image_dir = Path(image_dir)
        self.bbox_only = bbox_only
        self.fix_invalid_polygons = fix_invalid_polygons

        if not self.json_path.is_file():
            raise FileNotFoundError(f"Annotation file not found: {self.json_path}")
        if not self.image_dir.is_dir():
            raise FileNotFoundError(f"Image directory not found: {self.image_dir}")

        self.class_map = {}

    def _extract_spatial_data(self, anno):
        """
        A generator function for ingesting exactly one of at most two spatial
        attributes contained in any single annotation object from the input
        JSON.

        By default, we preference ingestion of the segmentation label over the
        bounding box ("bbox") label. You can optionally override this behavior by
        setting the bbox_only option to True.
        """
        if CocoKeys.SEG in anno and not self.bbox_only:
            try:
                pts = [list(zip(f[:-1:2], f[1::2])) for f in anno[CocoKeys.SEG]]
                poly = multipolygon_from_coords(pts, fix_invalid_polygons=self.fix_invalid_polygons)
                yield PixelLocationAttributeValue.from_geom(poly)
            except Exception as e:
                logger.warning(f"Skipping invalid segmentation in annotation {anno.get('id')}: {e}")

        elif CocoKeys.BBOX in anno:
            try:
                yield PixelLocationAttributeValue.from_geom(
                    polygon_from_left_top_width_height_coords(anno[CocoKeys.BBOX])
                )
            except Exception as e:
                logger.warning(f"Skipping invalid bbox in annotation {anno.get('id')}: {e}")

    def read(self) -> Tuple[List[AttributeRecord], List[ImageRecord]]:
        """
        Parses annotations and images, verifying integrity against the filesystem.

        Returns:
            Tuple[List[AttributeRecord], List[ImageRecord]]: verified image and attribute records.
        """
        try:
            with self.json_path.open() as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load coco annotations from {self.json_path}: {e}")

        # extract class-from-ID map and group annotations by image ID for O(1) lookup
        self.class_map = {c[CocoKeys.ID]: c[CocoKeys.NAME] for c in data.get(CocoKeys.CATS, [])}
        annos_map = {}
        for a in data.get(CocoKeys.ANNOS, []):
            # if this annotation's segmentation field is a polygon list, map to
            # it map to it from the ID of its containing image (for uploading)
            if not a.get("iscrowd"):
                annos_map.setdefault(a[CocoKeys.IMAGE_ID], []).append(a)

        imgs, attrs, seen = [], [], set()

        # iterate over images defined in JSON
        for i in data.get(CocoKeys.IMAGES, []):
            if (f_id := i.get(CocoKeys.ID)) in seen:
                continue

            seen.add(f_id)
            # verify file existence and integrity
            f_path = self.image_dir / i.get(CocoKeys.FILE_NAME, "")

            if f_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                logger.warning(f"Skipping image with unsupported extension: {f_path}")
                continue

            try:
                if not f_path.exists():
                    logger.warning(f"Image file not found: {f_path}")
                    continue
                with Image.open(f_path) as img:
                    # pixel dimensions
                    width, height = img.size
            except Exception as e:
                logger.error(f"Skipping corrupt or unreadable image {f_path}: {e}")
                continue

            imgs.append(
                ImageRecord(
                    data_file_id=str(f_id),
                    width=width,
                    height=height,
                    filename=str(f_path),
                    split="data",
                    extra_fields=i.get(CocoKeys.EXTRA_FIELDS, {}),
                )
            )

            # process annotations associated with this image
            for a in annos_map.get(f_id, []):
                if (cid := a.get(CocoKeys.CAT_ID)) not in self.class_map:
                    logger.warning(f"Skipping annotation with unknown category id {cid} in image {f_id}")
                    continue

                e_id = a.get(CocoKeys.EXTRA_FIELDS, {}).pop("entity_id", str(uuid4()))
                attrs.append(
                    AttributeRecord(
                        data_file_id=str(f_id),
                        entity_id=e_id,
                        attribute_id=str(OBJECT_CLASS_ATTRIBUTE_UUID),
                        attribute_name=OBJECT_CLASS_ATTRIBUTE_UUID.label,
                        value=self.class_map[cid],
                    )
                )

                # capture all valid geometries (seg AND bbox if both present)
                for g in self._extract_spatial_data(a):
                    attrs.append(AttributeRecord.from_attribute_value(str(f_id), g, entity_id=e_id))

                # add an additional attribute for each extra, 'metadata' field
                for k, v in a.get(CocoKeys.EXTRA_FIELDS, {}).items():
                    attrs.append(
                        AttributeRecord(
                            data_file_id=str(f_id),
                            entity_id=e_id,
                            attribute_id=k,
                            attribute_name="ToDo",
                            value=v,
                        )
                    )

        return imgs, attrs
