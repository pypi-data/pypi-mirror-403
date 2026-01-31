import logging
from pathlib import Path
from typing import List, Tuple
from uuid import uuid4

import yaml
from PIL import Image
from shapely.geometry import Polygon

from highlighter.client import PixelLocationAttributeValue
from highlighter.core import OBJECT_CLASS_ATTRIBUTE_UUID
from highlighter.datasets.base_models import AttributeRecord, ImageRecord
from highlighter.datasets.common import SUPPORTED_IMAGE_EXTENSIONS
from highlighter.datasets.interfaces import IReader

logger = logging.getLogger(__name__)


class YoloReader(IReader):
    """
    Parses a YOLO dataset, returning a comprehensive list of its images and attributes.

    This reader adheres to standard YOLO file organisation conventions and handles:
    - Multiple splits (train, val, test) with deduplication of files across splits.
    - Flexible image discovery within directories or file lists specified in the YAML configuration.
    - Resolution of label files in collocated, sibling, or otherwise mirrored "labels" directories.
    - Parsing of standard YOLO label format: <class_id> <x_center> <y_center> <width> <height> (each normalised).

    Requirements:
    - A single YAML configuration file defining "names" (class map) and paths for dataset splits.
    """

    format_name = "yolo"
    # conventional YOLO dataset split names
    SPLIT_KEYS = ("train", "val", "test")

    def __init__(self, yaml_path: Path, working_dir: Path = Path.cwd()):
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        try:
            self.cfg = yaml.safe_load(yaml_path.read_text()) or {}
        except Exception as e:
            raise ValueError(f"Invalid YAML in {yaml_path}: {e}")

        # resolve and validate dataset root
        self.root = (Path(working_dir) / self.cfg.get("path", "")).resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(f"Dataset root directory does not exist: {self.root}")

        # build object class map
        names = self.cfg.get("names", {})
        self.class_map = dict(enumerate(names)) if isinstance(names, list) else names

    def _resolve_label_path(self, img_path: Path) -> Path | None:
        """Robustly finds labels in collocated, sibling, or mirrored directories."""
        # check collocated (i.e., same folder)
        if (p := img_path.with_suffix(".txt")).exists():
            return p
        # check sibling "labels" folder (e.g. data/images/x.jpg -> data/labels/x.txt)
        if (p := img_path.parent.with_name("labels") / img_path.with_suffix(".txt").name).exists():
            return p
        # check deeper mirror (e.g. replacing "images" with "labels" anywhere in path)
        for key in ["images", "imgs", img_path.parent.name]:
            new_path_str = img_path.as_posix().replace(f"/{key}/", "/labels/")
            # verify uniqueness of new path and its existence before returning
            if new_path_str != str(img_path) and (p := Path(new_path_str).with_suffix(".txt")).exists():
                return p
        return None

    def read(self) -> Tuple[List[AttributeRecord], List[ImageRecord]]:
        """
        Reads the dataset splits defined in the configuration, preventing duplication.

        Iterates through 'train', 'val', and 'test' splits, identifying unique image files
        and their corresponding labels. Parses annotations into Highlighter-compatible
        records, handling missing or malformed files gracefully.

        Returns:
            Tuple[List[AttributeRecord], List[ImageRecord]]: A pair of lists containing
            the processed image records and their associated attribute records.
        """
        imgs, attrs = [], []
        # iterate over the existing configured splits (train/val/test)
        seen_splits = set()
        seen_files = set()
        for split in [k for k in self.SPLIT_KEYS if self.cfg.get(k)]:
            # do not read this split if it has already appeared under a different name
            if (split_signature := str(srcs := self.cfg[split])) in seen_splits:
                continue
            seen_splits.add(split_signature)
            # handle both a list of paths and a single path
            for src in [srcs] if isinstance(srcs, str) else srcs:
                p = (self.root / src).resolve()
                if not p.exists():
                    continue

                # find images in directory, listed in text file, or single file
                files = set()
                if p.is_dir():
                    # grab all images in this immediate directory
                    files.update(f for f in p.glob("*") if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS)
                elif p.suffix == ".txt":
                    # if text file path list, read and resolve each paths relative to YAML root
                    for line in p.read_text().splitlines():
                        if not line.strip():
                            continue

                        img_path = (self.root / line.strip()).resolve()
                        if img_path.exists():
                            files.add(img_path)
                        else:
                            logger.warning(f"Referenced file in {p.name} not found: {line}.")
                elif p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                    # if source is a direct image path
                    files.add(p)

                # sort file set for reproducible logging
                seen_files.update(new_files := {f.resolve() for f in files} - seen_files)
                for f in sorted(new_files):
                    try:
                        valid_labels = []
                        # build sanitised label set by only parsing lines with five tokens
                        if label_path := self._resolve_label_path(f):
                            valid_labels = [
                                t
                                for line in set(label_path.read_text().splitlines())
                                if len(t := line.split()) == 5
                            ]

                        f_uuid = uuid4()
                        # verify image integrity + get true dimensions for both
                        # metadata and bounding box drawing
                        with Image.open(f) as img:
                            w, h = img.size
                        imgs.append(
                            ImageRecord(
                                data_file_id=str(f_uuid), width=w, height=h, filename=str(f), split=split
                            )
                        )

                        # add attributes (boxes and classes)
                        for label in valid_labels:
                            try:
                                cls, cx, cy, bw, bh = (
                                    int(label[0]),
                                    float(label[1]),
                                    float(label[2]),
                                    float(label[3]),
                                    float(label[4]),
                                )
                            except ValueError:
                                logger.warning(f"Skipping non-numeric label in {label_path}: {label}")
                                continue
                            if cls not in self.class_map:
                                raise KeyError(
                                    f"Found class id '{cls}' in {label_path} that did not appear in the dataset .yaml"
                                )

                            eid = uuid4()
                            # append object class attribute
                            attrs.append(
                                AttributeRecord(
                                    data_file_id=str(f_uuid),
                                    entity_id=eid,
                                    attribute_id=str(OBJECT_CLASS_ATTRIBUTE_UUID),
                                    attribute_name=OBJECT_CLASS_ATTRIBUTE_UUID.label,
                                    value=self.class_map[cls],
                                )
                            )

                            # calculate top left x/y pixel location and true
                            # pixel width/height of bounding box
                            x, y = (cx - bw / 2) * w, (cy - bh / 2) * h
                            rw, rh = bw * w, bh * h
                            # append bounding box/geometry attribute
                            attrs.append(
                                AttributeRecord.from_attribute_value(
                                    str(f_uuid),
                                    PixelLocationAttributeValue.from_geom(
                                        Polygon([(x, y), (x + rw, y), (x + rw, y + rh), (x, y + rh)])
                                    ),
                                    eid,
                                )
                            )

                    except Exception as e:
                        # if we fail to parse any file, skip it and continue
                        logger.error(f"Encountered an issue processing {f}: {e}")
                        continue

        return imgs, attrs
