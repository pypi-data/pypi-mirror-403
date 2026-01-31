"""Motion measurement using optical flow."""

import logging
from collections import deque
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, Union
from uuid import UUID

from highlighter.core.exceptions import require_package

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError as _:
    plt = None

import numpy as np
from pydantic import BaseModel, model_validator

from highlighter.agent.capabilities import Capability, StreamEvent
from highlighter.agent.capabilities.image_to_scalar._neuflowv2 import (
    NeuFlowV2,
    flow_to_image,
)
from highlighter.client.base_models.annotation import Annotation
from highlighter.client.base_models.entity import Entity
from highlighter.client.base_models.observation import Observation
from highlighter.core import LabeledUUID
from highlighter.core.data_models import DataSample

__all__ = ["MotionMeasurer", "OpticalFlow", "MotionMeasurerCapability"]


DEFAULT_MODEL_PATH = Path.home() / ".cache" / "highlighter" / "models" / "neuflow_sintel.onnx"


class OpticalFlow(BaseModel):
    """
    A standalone optical flow class that calculates motion between consecutive frames.

    All preprocessing (Gaussian blur, resize) is handled inside the ONNX model,
    making this class a thin wrapper around NeuFlowV2.

    Args:
        model_path: Path to the optical flow model file.
        use_gpu: Whether to use GPU for inference.
        blur_kernel_size: Size of Gaussian blur kernel (3, 5, 7) or None to disable blur.
    """

    model_path: Union[str, Path] = DEFAULT_MODEL_PATH
    use_gpu: bool = True
    blur_kernel_size: Optional[int] = 3

    @model_validator(mode="after")
    def init(self):
        self._logger = logging.getLogger(__name__)
        self._estimator = self._load_model()
        self._prev_frame = None
        self._logger.info(f"Initialized OpticalFlow (use_gpu={self.use_gpu}, blur={self.blur_kernel_size})")
        return self

    def _load_model(self) -> NeuFlowV2:
        """Load the NeuFlowV2 optical flow model."""
        return NeuFlowV2(str(self.model_path), use_gpu=self.use_gpu, blur_kernel_size=self.blur_kernel_size)

    def update(self, image: np.ndarray) -> np.ndarray:
        """
        Update with a new image and return optical flow vectors.

        Args:
            image: Input image (H, W, 3) uint8 array.

        Returns:
            Flow vectors (H, W, 2) float32 array.
        """
        # Ensure uint8
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8) if image.max() <= 1.0 else image.astype(np.uint8)

        if self._prev_frame is None:
            self._prev_frame = image
            h, w = image.shape[:2]
            return np.zeros((h, w, 2), dtype=np.float32)

        flow_vectors = self._estimator(self._prev_frame, image)
        self._prev_frame = image

        return flow_vectors

    def reset(self):
        """Reset the optical flow state."""
        self._prev_frame = None

    @staticmethod
    def draw_flow(curr_frame: np.ndarray, flow: np.ndarray, step: int = 10) -> np.ndarray:
        """
        Draw optical flow vectors on a frame.

        Uses the Middlebury color scheme via flow_to_image and overlays on the frame.

        Args:
            curr_frame: Current frame (H, W, 3) uint8 array.
            flow: Optical flow (H, W, 2) float32 array.
            step: Grid step for sampling flow vectors.

        Returns:
            Frame with flow visualization (H, W, 3) uint8 array.
        """
        # Create flow color image
        flow_img = flow_to_image(flow)

        # Blend with original frame
        alpha = 0.6
        blended = (alpha * flow_img + (1 - alpha) * curr_frame).astype(np.uint8)

        return blended


class MotionMeasurer(BaseModel):
    """
    Compute motion measurement from video frames via optical flow.

    Usage:
        mm = MotionMeasurer(score_type=["mean", "median"], window_size=10)
        for idx, frame in enumerate(frame_generator):
            scores = mm.update(frame, idx)
            # {'mean': 0.23, 'median': 0.19}
    """

    score_type: List[Literal["sum", "mean", "median"]] = ["mean"]
    window_size: int = 20
    history_size: int = 40

    # OpticalFlow Args
    model_path: Union[str, Path] = DEFAULT_MODEL_PATH
    use_gpu: bool = True
    blur_kernel_size: Optional[int] = 3

    @model_validator(mode="after")
    def init(self):
        self._optical_flow_model = OpticalFlow(
            model_path=self.model_path,
            use_gpu=self.use_gpu,
            blur_kernel_size=self.blur_kernel_size,
        )

        self._score_names = ["sum", "mean", "median"]
        self._score_idxs = [self._score_names.index(a) for a in self.score_type]
        self._motion_averages = {
            self._score_names[i]: MovingAverage(self.window_size) for i in self._score_idxs
        }
        self._frame_idxs = deque(maxlen=self.history_size)
        self._motion_averages_history = {
            self._score_names[i]: deque(maxlen=self.history_size) for i in self._score_idxs
        }
        self._flow_vectors = None
        return self

    def _update_motion_scores(self, flow_vectors: np.ndarray):
        u, v = flow_vectors[..., 0], flow_vectors[..., 1]
        magnitude = np.sqrt(u**2 + v**2)
        motion_scores = (
            float(np.sum(magnitude)),
            float(np.mean(magnitude)),
            float(np.median(magnitude)),
        )

        for i in self._score_idxs:
            self._motion_averages[self._score_names[i]].update(motion_scores[i])

        for k, v in self._motion_averages.items():
            self._motion_averages_history[k].append(v.get_average())

    def get_latest_flow_vectors(self):
        return self._flow_vectors

    def update(self, image: np.ndarray, frame_idx: int) -> Dict[str, float]:
        """
        Process a new video frame and update motion statistics.

        Parameters
        ----------
        image : np.ndarray
            Current video frame (H, W, 3) uint8 array.
        frame_idx : int
            Frame index for tracking.

        Returns
        -------
        Dict[str, float]
            Mapping from score name to moving-average value.
        """
        self._frame_idxs.append(frame_idx)
        flow_vectors = self._optical_flow_model.update(image)
        self._flow_vectors = flow_vectors

        self._update_motion_scores(flow_vectors)

        return {k: v[-1] for k, v in self._motion_averages_history.items()}

    @require_package(plt, "matplotlib", "matplotlib")
    def get_motion_score_fig(self, select: Optional[List[str]] = None, width: int = 600, height: int = 550):
        plt.style.use("dark_background")

        if select is None:
            select = list(self._motion_averages.keys())

        assert all([s in self._motion_averages for s in select])

        fig, axies = plt.subplots(len(select), 1, figsize=(width / 100, height / 100), dpi=100)
        if not isinstance(axies, np.ndarray):
            axies = [axies]

        plot_colors = {
            "sum": "#00BFFF",
            "mean": "#00FF7F",
            "median": "#FFD700",
        }
        plot_colors = {k: v for k, v in plot_colors.items() if k in select}

        for i, (key, color) in enumerate(plot_colors.items()):
            ax = axies[i]
            scores = self._motion_averages_history[key]

            ax.plot(self._frame_idxs, scores, color=color, linewidth=2, alpha=0.9)
            ax.fill_between(self._frame_idxs, scores, alpha=0.3, color=color)

            ax.set_title(
                f"Movement Score ({key.title()})",
                fontsize=20,
                color="white",
                fontweight="bold",
            )
            ax.set_ylabel(key.title(), fontsize=20, color="white")
            ax.grid(True, alpha=0.4, color="gray", linestyle="-", linewidth=0.8)
            ax.set_facecolor("black")
            ax.tick_params(colors="white", labelsize=20)

        axies[-1].set_xlabel("Frame", fontsize=7, color="white")

        fig.patch.set_facecolor("black")
        fig.patch.set_alpha(0.9)
        plt.tight_layout()
        return fig


class MovingAverage:
    def __init__(self, window_size):
        if window_size <= 0:
            raise ValueError("Window size must be positive")
        self.window_size = window_size
        self.values = []
        self.sum = 0.0

    def update(self, value):
        self.values.append(value)
        self.sum += value

        if len(self.values) > self.window_size:
            self.sum -= self.values.pop(0)

        return self.get_average()

    def get_average(self):
        if not self.values:
            return 0.0
        return self.sum / len(self.values)


class MotionMeasurerCapability(Capability):
    class InitParameters(Capability.InitParameters):
        attribute_id: UUID
        object_class_id: UUID | str
        model_path: str = DEFAULT_MODEL_PATH
        score_type: Literal["mean", "sum", "median"] = "mean"
        window_size: int = 20
        use_gpu: bool = False
        blur_kernel_size: Optional[int] = 3

    class StreamParameters(InitParameters):
        entity_id: UUID
        crop: Optional[Tuple[float, float, float, float]] = None

    def __init__(self, context):
        super().__init__(context)

        if "|" in self.init_parameters.object_class_id:
            self.object_class_id = LabeledUUID.from_str(self.init_parameters.object_class_id)
        else:
            self.object_class_id = LabeledUUID.from_str(f"{self.init_parameters.object_class_id}|-")

    def start_stream(self, stream, stream_id, use_create_frame=True):
        kwargs = {"score_type": [self.init_parameters.score_type]}
        kwargs["model_path"] = self.init_parameters.model_path
        kwargs["use_gpu"] = self.init_parameters.use_gpu
        kwargs["blur_kernel_size"] = self.init_parameters.blur_kernel_size
        kwargs["window_size"] = self.init_parameters.window_size
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        stream.variables["_motion_score_model"] = MotionMeasurer(**kwargs)
        return super().start_stream(stream, stream_id, use_create_frame=use_create_frame)

    def stop_stream(self, stream, stream_id):
        return super().stop_stream(stream, stream_id)

    def process_frame(
        self, stream, data_samples: List[DataSample], **kwargs
    ) -> Tuple[StreamEvent, Union[Dict, str]]:
        parameters = self.stream_parameters(stream.stream_id)
        if len(data_samples) > 1:
            self.logger.warning(
                f"Expected only a single DataFile, got {len(data_samples)}. Processing data_samples[0] only."
            )

        ds = data_samples[0]
        w, h = ds.wh

        if parameters.crop is not None:
            if isinstance(parameters.crop[0], float):
                x0 = int(parameters.crop[0] * w)
                y0 = int(parameters.crop[1] * h)
                x1 = int(parameters.crop[2] * w)
                y1 = int(parameters.crop[3] * h)
                anno_tuple = (x0, y0, x1, y1)
            else:
                anno_tuple = parameters.crop
            img = ds.crop_content([parameters.crop])[0]
        else:
            anno_tuple = (0, 0, w, h)
            img = ds.content

        score = stream.variables["_motion_score_model"].update(img, ds.media_frame_index)[
            parameters.score_type
        ]
        attribute_id = LabeledUUID.from_str(f"{parameters.attribute_id}|motion_score")
        score_obs = Observation.make_scalar_observation(
            score,
            attribute_id,
            occurred_at=ds.recorded_at,
            pipeline_element_name=self.name,
            frame_id=ds.media_frame_index,
        )
        obj_obs = Observation.make_object_class_observation(
            object_class_uuid=self.object_class_id,
            object_class_value=self.object_class_id.label,
            confidence=1.0,
            occurred_at=ds.recorded_at,
            pipeline_element_name=self.name,
            frame_id=ds.media_frame_index,
        )
        a = Annotation.from_left_top_right_bottom_box(
            anno_tuple,
            1.0,
            data_sample=ds,
            observations=[score_obs, obj_obs],
        )

        entity = Entity(id=parameters.entity_id, annotations=[a])
        entities = {parameters.entity_id: entity}

        for entity_id, entity in entities.items():
            for anno in entity.annotations:
                for obs in anno.observations:
                    if hasattr(obs, "attribute_id") and "motion_score" in str(obs.attribute_id):
                        self.logger.verbose(
                            f"motion_measurer output: entity={entity_id}, frame={obs.datum_source.frame_id}, attr={obs.attribute_id}, value={obs.value}, type={type(obs.value)}"
                        )

        return StreamEvent.OKAY, {"entities": entities}
