"""
Prepend Gaussian blur and resize preprocessing to NeuFlow ONNX model.

This creates a single ONNX model that:
1. Takes raw uint8 HWC images as input
2. Applies Gaussian blur (kernel provided at runtime)
3. Resizes to model input dimensions
4. Runs optical flow estimation
5. Resizes flow output back to original dimensions

Usage:
    python -m highlighter.agent.capabilities.image_to_scalar._neuflow_preprocessing \
        input_model.onnx output_model.onnx
"""

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

MAX_KERNEL_SIZE = 7


def make_gaussian_kernel(kernel_size: int, sigma: float) -> np.ndarray:
    """Create a 2D Gaussian kernel for depthwise convolution."""
    coords = np.arange(kernel_size) - kernel_size // 2
    g = np.exp(-(coords**2) / (2 * sigma**2))
    kernel_2d = np.outer(g, g)
    kernel_2d = kernel_2d / kernel_2d.sum()
    # Shape for depthwise conv: (out_channels=3, in_channels/groups=1, H, W)
    kernel_4d = np.tile(kernel_2d[np.newaxis, np.newaxis, :, :], (3, 1, 1, 1))
    # Zero-pad to max kernel size
    if kernel_size < MAX_KERNEL_SIZE:
        pad = (MAX_KERNEL_SIZE - kernel_size) // 2
        kernel_4d = np.pad(kernel_4d, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
    return kernel_4d.astype(np.float32)


def make_identity_kernel() -> np.ndarray:
    """Create identity kernel (no-op convolution)."""
    kernel = np.zeros((MAX_KERNEL_SIZE, MAX_KERNEL_SIZE), dtype=np.float32)
    kernel[MAX_KERNEL_SIZE // 2, MAX_KERNEL_SIZE // 2] = 1.0
    return np.tile(kernel[np.newaxis, np.newaxis, :, :], (3, 1, 1, 1))


def _make_preprocess_nodes(
    input_name: str,
    output_name: str,
    model_h: int,
    model_w: int,
    prefix: str,
) -> list:
    """Create preprocessing nodes for a single image input."""
    nodes = []
    pad = MAX_KERNEL_SIZE // 2

    # HWC -> CHW
    nodes.append(
        helper.make_node(
            "Transpose",
            inputs=[input_name],
            outputs=[f"{prefix}chw"],
            perm=[2, 0, 1],
            name=f"{prefix}transpose",
        )
    )

    # Add batch dim: CHW -> BCHW
    nodes.append(
        helper.make_node(
            "Unsqueeze",
            inputs=[f"{prefix}chw", "unsqueeze_axes"],
            outputs=[f"{prefix}bchw"],
            name=f"{prefix}unsqueeze",
        )
    )

    # Cast uint8 -> float32
    nodes.append(
        helper.make_node(
            "Cast",
            inputs=[f"{prefix}bchw"],
            outputs=[f"{prefix}float"],
            to=TensorProto.FLOAT,
            name=f"{prefix}cast",
        )
    )

    # Normalize [0, 255] -> [0, 1]
    nodes.append(
        helper.make_node(
            "Div",
            inputs=[f"{prefix}float", "scale_255"],
            outputs=[f"{prefix}normalized"],
            name=f"{prefix}normalize",
        )
    )

    # Gaussian blur via depthwise convolution (kernel is a runtime input)
    nodes.append(
        helper.make_node(
            "Conv",
            inputs=[f"{prefix}normalized", "blur_kernel"],
            outputs=[f"{prefix}blurred"],
            kernel_shape=[MAX_KERNEL_SIZE, MAX_KERNEL_SIZE],
            pads=[pad, pad, pad, pad],
            group=3,
            name=f"{prefix}blur",
        )
    )

    # Resize to model input dimensions
    nodes.append(
        helper.make_node(
            "Resize",
            inputs=[f"{prefix}blurred", "", "", "resize_shape"],
            outputs=[output_name],
            mode="linear",
            coordinate_transformation_mode="asymmetric",
            name=f"{prefix}resize",
        )
    )

    return nodes


def prepend_preprocessing_to_neuflow(
    neuflow_path: str,
    output_path: str,
) -> None:
    """
    Modify NeuFlow ONNX model to include preprocessing.

    New model signature:
        Inputs:
            - prev_image: (H, W, 3) uint8
            - curr_image: (H, W, 3) uint8
            - blur_kernel: (3, 1, K, K) float32 - Gaussian or identity kernel
        Outputs:
            - flow: (H, W, 2) float32
    """
    # Load original model
    original_model = onnx.load(neuflow_path)
    original_graph = original_model.graph

    # Get model input dimensions from original model
    input_shape = original_graph.input[0].type.tensor_type.shape
    model_h = input_shape.dim[2].dim_value
    model_w = input_shape.dim[3].dim_value
    print(f"NeuFlow model input size: {model_h}x{model_w}")

    # Build new nodes list
    new_nodes = []
    new_initializers = list(original_graph.initializer)

    # --- Preprocessing for prev_image ---
    new_nodes.extend(
        _make_preprocess_nodes(
            input_name="prev_image",
            output_name="prev_processed",
            model_h=model_h,
            model_w=model_w,
            prefix="prev_",
        )
    )

    # --- Preprocessing for curr_image ---
    new_nodes.extend(
        _make_preprocess_nodes(
            input_name="curr_image",
            output_name="curr_processed",
            model_h=model_h,
            model_w=model_w,
            prefix="curr_",
        )
    )

    # Add shared initializers (constants used by preprocessing)
    new_initializers.extend(
        [
            numpy_helper.from_array(np.array([0], dtype=np.int64), name="unsqueeze_axes"),
            numpy_helper.from_array(np.array([0], dtype=np.int64), name="squeeze_axes"),
            numpy_helper.from_array(np.array([255.0], dtype=np.float32), name="scale_255"),
            numpy_helper.from_array(np.array([1, 3, model_h, model_w], dtype=np.int64), name="resize_shape"),
        ]
    )

    # --- Rename original model inputs to connect to preprocessing outputs ---
    original_input_names = [inp.name for inp in original_graph.input]
    print(f"Original input names: {original_input_names}")

    input_mapping = {
        original_input_names[0]: "prev_processed",
        original_input_names[1]: "curr_processed",
    }

    # Copy and rename original model nodes
    for node in original_graph.node:
        new_node = onnx.NodeProto()
        new_node.CopyFrom(node)

        # Rename inputs if they match original model inputs
        new_inputs = []
        for inp in node.input:
            new_inputs.append(input_mapping.get(inp, inp))
        new_node.ClearField("input")
        new_node.input.extend(new_inputs)

        new_nodes.append(new_node)

    # --- Postprocessing: resize flow back to original dimensions ---
    original_output_name = original_graph.output[0].name

    # Get original image dimensions for resizing output
    new_nodes.append(
        helper.make_node(
            "Shape",
            inputs=["prev_image"],
            outputs=["input_shape"],
            name="get_input_shape",
        )
    )

    # Extract H, W from shape (H, W, 3)
    new_nodes.append(
        helper.make_node(
            "Slice",
            inputs=["input_shape", "slice_start", "slice_end"],
            outputs=["hw_shape"],
            name="extract_hw",
        )
    )
    new_initializers.append(numpy_helper.from_array(np.array([0], dtype=np.int64), name="slice_start"))
    new_initializers.append(numpy_helper.from_array(np.array([2], dtype=np.int64), name="slice_end"))

    # Build output shape: [1, 2, H, W]
    new_nodes.append(
        helper.make_node(
            "Concat",
            inputs=["batch_channels", "hw_shape"],
            outputs=["output_resize_shape"],
            axis=0,
            name="build_output_shape",
        )
    )
    new_initializers.append(numpy_helper.from_array(np.array([1, 2], dtype=np.int64), name="batch_channels"))

    # Resize flow to original dimensions
    new_nodes.append(
        helper.make_node(
            "Resize",
            inputs=[original_output_name, "", "", "output_resize_shape"],
            outputs=["flow_resized"],
            mode="linear",
            coordinate_transformation_mode="asymmetric",
            name="resize_flow_output",
        )
    )

    # Squeeze batch dim: (1, 2, H, W) -> (2, H, W)
    new_nodes.append(
        helper.make_node(
            "Squeeze",
            inputs=["flow_resized", "squeeze_axes"],
            outputs=["flow_squeezed"],
            name="squeeze_flow",
        )
    )

    # Transpose: (2, H, W) -> (H, W, 2)
    new_nodes.append(
        helper.make_node(
            "Transpose",
            inputs=["flow_squeezed"],
            outputs=["flow_output"],
            perm=[1, 2, 0],
            name="transpose_flow",
        )
    )

    # --- Create new graph ---
    new_inputs = [
        helper.make_tensor_value_info("prev_image", TensorProto.UINT8, ["H", "W", 3]),
        helper.make_tensor_value_info("curr_image", TensorProto.UINT8, ["H", "W", 3]),
        helper.make_tensor_value_info(
            "blur_kernel", TensorProto.FLOAT, [3, 1, MAX_KERNEL_SIZE, MAX_KERNEL_SIZE]
        ),
    ]

    new_outputs = [
        helper.make_tensor_value_info("flow_output", TensorProto.FLOAT, ["H", "W", 2]),
    ]

    new_graph = helper.make_graph(
        nodes=new_nodes,
        name="neuflow_with_preprocessing",
        inputs=new_inputs,
        outputs=new_outputs,
        initializer=new_initializers,
    )

    # Create new model
    new_model = helper.make_model(new_graph, opset_imports=original_model.opset_import)
    new_model.ir_version = original_model.ir_version

    # Validate and save
    onnx.checker.check_model(new_model)
    onnx.save(new_model, output_path)
    print(f"Saved modified model to: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add preprocessing to NeuFlow model")
    parser.add_argument("input_model", help="Path to original NeuFlow ONNX model")
    parser.add_argument("output_model", help="Path for output model with preprocessing")

    args = parser.parse_args()

    prepend_preprocessing_to_neuflow(args.input_model, args.output_model)
