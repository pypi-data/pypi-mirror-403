from collections import defaultdict

import numpy as np
import ultralytics


class WeightedSamplingMixin:
    """Shared weighted-sampling utilities for classification/detection/segmentation datasets."""

    def _init_weighted_sampling(self):

        self.train_mode = (
            "train" in str(getattr(self, "prefix", "")).lower()
        )  # standardise how we detect train mode (works for both datasets)

        self.counts = self.count_instances()
        self.class_weights = self.calculate_class_weights(self.counts)
        self.item_weights = self.calculate_item_weights(self.class_weights)
        self.probabilities = self.normalize_probs(self.item_weights)

    def calculate_class_weights(self, counts: np.ndarray) -> np.ndarray:
        total = float(np.sum(counts))
        w = total / counts.astype(np.float64)
        return w

    def normalize_probs(self, weights: np.ndarray) -> np.ndarray:
        s = float(np.sum(weights))
        if s <= 0 or not np.isfinite(s):
            print("Falling back to uniform sampling")
            return np.ones_like(weights, dtype=np.float64) / max(len(weights), 1)

        p = weights / s
        p = np.clip(p, 0.0, 1.0)  # numerical safety
        p = p / float(np.sum(p))  # renormalise after clipping
        return p.astype(np.float64)

    def weighted_index(self, n: int) -> int:
        return int(np.random.choice(n, p=self.probabilities))


class WeightedClassificationDataset(ultralytics.data.dataset.ClassificationDataset, WeightedSamplingMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_weighted_sampling()

    def count_instances(self):
        """
        Count the number of instances per class

        Returns:
            dict: A dict containing the counts for each class.
        """
        counts = defaultdict(int)
        for _, label, _, _ in self.samples:
            counts[label] += 1

        if counts:
            max_label = max(counts.keys())
        else:
            max_label = -1

        counts = np.array([counts[i] for i in range(max_label + 1)], dtype=np.float64)
        counts[counts == 0] = 1.0
        return counts

    def calculate_item_weights(self, class_weights: np.ndarray) -> np.ndarray:
        weights = []

        for sample in self.samples:
            label = int(sample[1])  # class label for this sample
            weight = class_weights[label]  # lookup weight for that class
            weights.append(weight)

        return np.array(weights, dtype=np.float64)

    def __getitem__(self, index):
        """
        Return transformed label information based on the sampled index.
        """
        # Don't use for validation
        if not self.train_mode:
            return super().__getitem__(index)
        else:
            index = self.weighted_index(len(self.samples))

            # print(f"INDEX: {index}")
            return super().__getitem__(index)


class WeightedClassificationTrainer(ultralytics.models.yolo.classify.train.ClassificationTrainer):

    def build_dataset(self, img_path: str, mode: str = "train", batch=None):
        if mode == "train":
            return WeightedClassificationDataset(root=img_path, args=self.args, augment=True, prefix=mode)
        else:
            return ultralytics.data.dataset.ClassificationDataset(
                root=img_path, args=self.args, augment=False, prefix=mode
            )


class WeightedDetectionDataset(ultralytics.data.dataset.YOLODataset, WeightedSamplingMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_weighted_sampling()

    def _get_image_classes(self, label_item) -> np.ndarray:

        if isinstance(label_item, dict) and "cls" in label_item:
            cls = label_item["cls"]
            try:
                cls = np.array(cls).astype(int).reshape(-1)
            except Exception:
                return np.array([], dtype=int)
            return cls
        return np.array([], dtype=int)

    def count_instances(self) -> np.ndarray:

        counts = defaultdict(int)

        for lb in self.labels:  # list[dict]
            cls = self._get_image_classes(lb)
            if cls.size == 0:
                continue
        nc = int(getattr(self, "nc", 0) or 0)
        arr = np.array([counts[i] for i in range(nc)], dtype=np.float64)

        arr[arr == 0] = 1.0  # avoid division by zero for missing classes
        return arr

    def calculate_item_weights(self, class_weights: np.ndarray) -> np.ndarray:
        n = len(self.labels)
        img_w = np.ones(n, dtype=np.float64)

        for i, lb in enumerate(self.labels):
            cls = self._get_image_classes(lb)
            if cls.size == 0:
                img_w[i] = 1.0
                continue

            cls = cls[(cls >= 0) & (cls < len(class_weights))]
            if cls.size == 0:
                img_w[i] = 1.0
                continue

            img_w[i] = float(np.mean(class_weights[cls]))

        return img_w

    def __getitem__(self, index):
        if not self.train_mode:
            return super().__getitem__(index)

        index = self.weighted_index(len(self.labels))
        # print(f"INDEX: {index}")  # debug
        return super().__getitem__(index)


class WeightedDetectionTrainer(ultralytics.models.yolo.detect.train.DetectionTrainer):

    def build_dataset(self, img_path: str, mode: str = "train", batch=None):
        if mode == "train":
            return WeightedDetectionDataset(
                img_path=img_path,
                imgsz=self.args.imgsz,
                batch_size=batch,
                augment=True,
                hyp=self.args,
                rect=False,
                stride=32,
                pad=0.0,
                single_cls=self.args.single_cls,
                data=self.data,
                prefix=mode,
            )
        else:
            return ultralytics.data.dataset.YOLODataset(
                img_path=img_path,
                imgsz=self.args.imgsz,
                batch_size=batch,
                augment=False,
                hyp=self.args,
                rect=True,
                stride=32,
                pad=0.5,
                single_cls=self.args.single_cls,
                data=self.data,
                prefix=mode,
            )
