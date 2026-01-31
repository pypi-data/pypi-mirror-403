from datetime import datetime
from pathlib import Path

import click
import yaml
from pydantic import BaseModel

from highlighter.cli.common import CommonOptions

from ..client import get_latest_assessments_gen, multithread_graphql_file_download
from ..client.ingestion_setup import bootstrap_ingestion
from ..client.tasks import add_files_to_order
from ..datasets import (
    SUPPORTED_SPLIT_FNS,
    CocoWriter,
    Dataset,
    DatasetFormat,
    HighlighterAssessmentsWriter,
    YoloWriter,
    get_reader,
    get_split_fn,
)

TASK_CREATION_BATCH_SIZE = 1000


def _download_data_files(client, data_file_ids, data_file_dir):
    if data_file_dir is not None:
        multithread_graphql_file_download(
            client,
            data_file_ids,
            data_file_dir,
        )


def _combine_datasets(ctx):
    client = ctx.obj["client"]
    page_size = ctx.obj["page_size"]
    dataset_splits = ctx.obj["dataset_splits"]

    downloaded = {}
    datasets = []
    for dataset_id, split in dataset_splits:
        if dataset_id in downloaded:
            ds = Dataset(
                annotations_df=downloaded[dataset_id].annotations_df.copy(),
                data_files_df=downloaded[dataset_id].data_files_df.copy(),
            )
        else:
            ds = Dataset.read_from(
                dataset_format=DatasetFormat.HIGHLIGHTER_DATASET,
                client=client,
                dataset_id=dataset_id,
                page_size=page_size,
            )
        ds.data_files_df.split = split
        datasets.append(ds)
        downloaded[dataset_id] = ds

    return Dataset.combine(datasets)


@click.group("dataset")
@click.pass_context
def dataset_group(ctx):
    pass


@dataset_group.command(
    "create",
    help="""
Create a Dataset in Highlighter

\b
Note: If using the --dataset-id param. There are no safety rails! That is to
say; the cli will allow duplicate assessments and data_files if you ask it to.

  ie: If dataset 123 has data_file 456 and workflow 789 also has data_file 456 the
  assessments for both will be added to the dataset.

Typically you would use the --dataset-id param if you wanted to combine 2 or
more datasets, or combine some new data from a workflow with an existing dataset.
In which case a new dataset would be created that simply has all assessments
appended together.
        """,
)
@click.option(
    "-n",
    "--name",
    type=str,
    required=True,
)
@click.option(
    "-w",
    "--workflow-id",
    type=int,
    required=False,
    default=None,
    multiple=True,
)
@click.option(
    "-oid",
    "--object-class-id",
    type=int,
    required=False,
    default=None,
    multiple=True,
)
@click.option(
    "-uid",
    "--user-id",
    type=int,
    required=False,
    default=None,
    multiple=True,
)
@click.option(
    "-did",
    "--dataset-id",
    type=int,
    required=False,
    default=None,
    multiple=True,
    help=(
        "Add assessments from existing dataset(s), see Note in help string "
        " for more context and a warrning."
    ),
)
@click.option(
    "--split-type",
    type=click.Choice(SUPPORTED_SPLIT_FNS.keys()),
    required=False,
    default="RandomSplitter",
    show_default=True,
)
@click.option(
    "--split-seed",
    type=int,
    required=False,
    default=42,
    show_default=True,
)
@click.option(
    "--split-frac",
    type=click.Tuple([str, float]),
    required=False,
    multiple=True,
    default=[("data", 1.0)],
    show_default=True,
)
@click.option(
    "-c",
    "--classes-of-interest",
    type=str,
    required=False,
    default=None,
    multiple=True,
    help="Object class uuids to consider when validating splits",
)
@click.option(
    "--page-size",
    type=int,
    required=False,
    default=200,
    help="Page Size used when fetching Assessments from Highlighter",
)
@click.pass_context
def create(
    ctx,
    name,
    workflow_id,
    object_class_id,
    user_id,
    dataset_id,
    split_type,
    split_seed,
    split_frac,
    classes_of_interest,
    page_size,
):
    client = ctx.obj["client"]

    status = 0  # completed
    query_args = dict(
        workflowId=workflow_id,
        objectClassId=object_class_id,
        userId=user_id,
        status=status,
        annotationStatus="HAS_ANNOTATIONS",
    )

    def not_empty(v):
        if v is None:
            return False
        if v == ():
            return False
        if v == []:
            return False
        return True

    query_args = {k: v for k, v in query_args.items() if not_empty(v)}

    datasets = []
    if query_args:
        latest_subs_gen = get_latest_assessments_gen(
            client,
            page_size=page_size,
            **query_args,
        )

        reader = get_reader("highlighter_assessments")(latest_subs_gen)
        ds = Dataset.load_from_reader(reader)
        datasets.append(ds)

    dataset_description_fields = []
    if dataset_id:
        # add to query_args here because datasetId is not a valid
        # arg to get_latest_assessments_gen, but we still want it
        # to appear in the Highlighter Dataset description.
        query_args["datasetId"] = dataset_id
        dataset_list = [
            Dataset.read_from(
                dataset_format=DatasetFormat.HIGHLIGHTER_DATASET,
                client=client,
                dataset_id=ds_id,
            )
            for ds_id in dataset_id
        ]

        datasets.extend(dataset_list)

        def get_dataset_url(id, client=client):
            return client.endpoint_url.replace("graphql", f"datasets/{id}")

        def get_dataset_name(id, client=client):
            class DatasetNameOnly(BaseModel):
                name: str

            name = client.dataset(
                return_type=DatasetNameOnly,
                id=id,
            ).name
            return name.replace("_", "\\_")

        base_dataset_links = [
            f"  - [{id}]({get_dataset_url(id)}): {get_dataset_name(id)}" for id in dataset_id
        ]
        base_dataset_links_str = "\n".join(base_dataset_links)
        dataset_description_fields.append(("Base Datasets", base_dataset_links_str))

    dataset = Dataset.combine(datasets)
    if classes_of_interest:
        adf = dataset.annotations_df
        ddf = dataset.data_files_df

        adf = adf[adf.value.isin(classes_of_interest)]
        ddf = ddf[ddf.data_file_id.isin(adf.data_file_id.unique())]
        dataset.annotations_df = adf
        dataset.data_files_df = ddf

    split_names = [s[0] for s in split_frac]
    fracs = [s[1] for s in split_frac]
    splitter = get_split_fn(split_type)(split_seed, fracs, split_names)

    dataset.apply_split(splitter)

    split_args = {
        "type": splitter.__class__.__name__,
        "seed": splitter.seed,
        "fracs": splitter.fracs,
        "names": splitter.names,
    }

    split_str = yaml.safe_dump(split_args)
    split_str = f"<pre>" + split_str + "</pre> \n"

    query_str = yaml.safe_dump(query_args)
    query_str = f"<pre>" + query_str + "</pre> \n"

    # List of tuples with e[0] being the heading and e[1]
    # being the content. This will be rendered as Markdown
    # in the publish_to_highlighter function.
    dataset_description_fields.extend(
        [
            ("Query", query_str),
            ("Split", split_str),
        ]
    )

    dataset.publish_to_highlighter(
        client,
        name,
        dataset_description_fields=dataset_description_fields,
        split_fracs={s: f for s, f in zip(split_names, fracs)},
    )


def _resolve_dataset_name(ctx, local_name, default_name):
    """
    Helper to enforce a single invocation of the --name/-n flag across
    `hl dataset upload FORMAT` commands.
    """
    if ctx.obj.get("dataset_name") and local_name:
        raise click.UsageError("The --name/-n flag should be used no more than once.")

    return ctx.obj.get("dataset_name") or local_name or default_name


def _upload_impl(ctx, ds, name, class_map=None):
    """
    Format-agnostic implementation of dataset upload logic.

    Args:
        ctx: context from click
        ds: a loaded Dataset object
        name: name of the dataset to create on the server
        class_map: optional dict of class_id -> class_name derived from readers.
    """
    obj_classes = set()
    if class_map:
        obj_classes.update(class_map.values())
    elif "value" in ds.annotations_df.columns:
        obj_classes.update(v for v in ds.annotations_df["value"].dropna().unique() if isinstance(v, str))

    # TODO: roll back workflow and data source creation on failure
    # create the project, workflow, etc. on the server
    client = ctx.obj["client"]
    infrastructure = bootstrap_ingestion(client, name, list(obj_classes))

    click.echo("Uploading images to new data source...")
    ds.upload_data_files(client, data_source_id=infrastructure.data_source_id, progress=True)

    # create task/assessment placeholders and get the mapping of
    # data_file_id -> assessment_id
    file_ids = ds.data_files_df["data_file_id"].dropna().unique().tolist()
    # ensure IDs are passed as strings to the API, handling floats if necessary
    file_ids = [str(int(f)) if isinstance(f, (int, float)) else str(f) for f in file_ids]

    click.echo(f"Preparing assessment submissions for {len(file_ids)} files...")
    task_map = {}
    for i in range(0, len(file_ids), TASK_CREATION_BATCH_SIZE):
        batch = file_ids[i : i + TASK_CREATION_BATCH_SIZE]
        task_map.update(add_files_to_order(client, infrastructure.order_id, batch))

    # wrap each image from our dataset and its associated attributes in a
    # Highlighter Annotation, and push it to web as a task
    HighlighterAssessmentsWriter(client, workflow_id=infrastructure.workflow_id, task_lookup=task_map).write(
        ds
    )

    # homogenise any distinct split names
    ds.data_files_df["split"] = "data"
    # create new dataset on web comprising all of the
    ds.publish_to_highlighter(client, f"{name}_{datetime.now().strftime('%H%M%S')}", split_fracs={"data": 1})
    click.echo(f"\nUpload complete.")


@dataset_group.group("upload", subcommand_metavar="FORMAT")
@click.option(
    "--name", "-n", required=False, default=None, help="The name of the new dataset to create in Highlighter."
)
@click.pass_context
def upload(ctx, name):
    """
    Upload a local object detection dataset to Highlighter.

    This command requires a FORMAT argument (one of 'yolo' or 'coco')
    in order to parse your dataset correctly.
    """
    ctx.ensure_object(dict)
    ctx.obj["dataset_name"] = name


# TODO:
# Two new options:
# - Provide a list of split/partition names defined in the YAML to ingest as a single dataset.
# - If previous option disabled, users can manually qualify 'image dir, label dir' pairs.
#   - We suggest this because at present, the standard YOLO schema for YAML files denotes each
#     split by its *images* directory--no mention of that split's corresponding label directory
#     exists.


@upload.command("yolo")
@click.argument("yaml_path", type=click.Path(exists=True, path_type=Path, resolve_path=True, dir_okay=False))
@click.option(
    "--name",
    "-n",
    required=False,
    default=None,
    help="The name of the new dataset to create in Highlighter.",
)
@click.option(
    "--working-directory",
    "-d",
    "working_dir",
    type=click.Path(exists=True, path_type=Path, resolve_path=True, file_okay=False),
    default=Path.cwd(),
    help="Base directory from which to interpret relative paths in the YAML file.",
)
@click.pass_context
def upload_yolo(ctx, yaml_path, working_dir, name):
    """
    Upload a YOLO-formatted dataset.

    YAML_PATH: Path to the data.yaml file definition.
    """
    dataset_name = _resolve_dataset_name(ctx, name, "YOLO Dataset")

    reader = get_reader("yolo")(yaml_path, working_dir)
    ds = Dataset.load_from_reader(reader)

    _upload_impl(ctx, ds, name=dataset_name, class_map=reader.class_map)


@upload.command("coco")
@click.argument(
    "json_path",
    required=False,
    type=click.Path(exists=True, path_type=Path, resolve_path=True, dir_okay=False),
)
@click.argument(
    "image_dir",
    required=False,
    type=click.Path(exists=True, path_type=Path, resolve_path=True, file_okay=False),
)
@click.option(
    "--name",
    "-n",
    required=False,
    default=None,
    help="The name of the new dataset to create in Highlighter.",
)
@click.option(
    "--input",
    "-i",
    "additional_splits",
    type=(
        click.Path(exists=True, path_type=Path, resolve_path=True, dir_okay=False),
        click.Path(exists=True, path_type=Path, resolve_path=True, file_okay=False),
    ),
    multiple=True,
    required=False,
    help="""
    Submit *additional* (json_path, image_dir) pairs for ingestion (i.e., prepend --input/-i to every pair after the first).
    """,
)
@click.option(
    "--bbox-only",
    is_flag=True,
    help="Ignore segmentation data and only import bounding boxes.",
)
@click.pass_context
def upload_coco(ctx, json_path, image_dir, name, additional_splits, bbox_only):
    """
    Upload a COCO-formatted dataset.

    You can upload multiple JSON files (e.g. train and val) by repeating the --input flag.

    \b
    Example:

        hl dataset upload -n my_ds coco train.json ./train_imgs -i val.json ./val_imgs
    """
    dataset_name = _resolve_dataset_name(ctx, name, "COCO Dataset")

    # collect all pairs of (json_path, image_dir)
    all_pairs = list(additional_splits)
    if json_path and image_dir:
        all_pairs.append((json_path, image_dir))
    elif json_path or image_dir:
        raise click.UsageError("Must provide both JSON_PATH and IMAGE_DIR if using positional arguments.")

    if not all_pairs:
        raise click.UsageError(
            "No datasets provided. Please specify JSON_PATH and IMAGE_DIR or use --input/-i."
        )

    datasets = []
    class_maps = []
    for j_path, i_dir in all_pairs:
        click.echo(f"Loading {j_path}...")
        reader = get_reader("coco")(Path(j_path), image_dir=Path(i_dir), bbox_only=bbox_only)
        class_maps.append(reader.class_map)
        datasets.append(Dataset.load_from_reader(reader))

    if not datasets:
        raise click.UsageError("No datasets loaded.")

    # combine all loaded COCO parts into one Dataset,
    # and all class maps into one map
    combined_ds = Dataset.combine(datasets)
    combined_class_map = {}
    for m in class_maps:
        combined_class_map.update(m)

    _upload_impl(ctx, combined_ds, dataset_name, class_map=combined_class_map)


@click.group("read")
@click.option(
    "-i",
    "--dataset-ids",
    type=str,
    required=False,
    multiple=True,
    default=[],
    show_default=True,
    help=" int or int:str --> ID or ID:SPLIT",
)
@click.option(
    "--page-size",
    type=int,
    required=False,
    default=None,
    show_default=True,
)
@click.pass_context
def read_group(ctx, dataset_ids, page_size):
    """Read Datasets from Highlighter and write to local disk.

    If page_size is None, the page_size is set from:
        HighlighterRuntimeConfig.default_pagination_page_size

    For help with each specific output format use:

    \b
      hl dataset read coco|yolo|... --help

    \b
    By default Datasets spits are all set to 'data' to assign
    a split to a dataset use --dataset-id ID:SPLIT

    \b
    Example:
      read datasets 111 and 222, assign 111 to 'train' split and
      222 to 'val' split then write to yolo detection format

    \b
      hl dataset read -i 111:train -i 204:val yolo -t detection my_output
    """
    ctx.obj["page_size"] = page_size if page_size is not None else ctx.obj["hl_cfg"].pagination_page_size

    if all([":" in i for i in dataset_ids]):
        dataset_splits = [i.split(":") for i in dataset_ids]
        dataset_splits = [(int(id), split) for id, split in dataset_splits]
    else:
        dataset_splits = [(int(i), "data") for i in dataset_ids]
    ctx.obj["dataset_splits"] = dataset_splits


@read_group.command("hdf")
@CommonOptions.annotations_dir
@CommonOptions.data_file_dir
@click.pass_context
def write_hdf(ctx, annotations_dir, data_file_dir):
    filestem = "-".join([str(i[0]) for i in ctx.obj["dataset_splits"]])
    filename = f"{filestem}.hdf"

    hdf_path = annotations_dir / filename
    combined_dataset = _combine_datasets(ctx)
    combined_dataset.write_hdf(hdf_path)

    data_file_ids = list(combined_dataset.data_files_df.data_file_id.unique())
    client = ctx.obj["client"]
    _download_data_files(client, data_file_ids, data_file_dir)


@read_group.command("json")
@CommonOptions.annotations_dir
@CommonOptions.data_file_dir
@click.pass_context
def write_json(ctx, annotations_dir, data_file_dir):
    filestem = "-".join([str(i[0]) for i in ctx.obj["dataset_splits"]])
    filename = f"{filestem}.json"

    json_path = annotations_dir / filename
    combined_dataset = _combine_datasets(ctx)
    combined_dataset.write_json(json_path)

    data_file_ids = list(combined_dataset.data_files_df.data_file_id.unique())
    client = ctx.obj["client"]
    _download_data_files(client, data_file_ids, data_file_dir)


@read_group.command(CocoWriter.format_name)
@CommonOptions.annotations_dir
@CommonOptions.data_file_dir
@click.pass_context
def write_coco(ctx, annotations_dir, data_file_dir):
    writer = CocoWriter(annotations_dir)

    combined_dataset = _combine_datasets(ctx)

    writer.write(combined_dataset)
    data_file_ids = list(combined_dataset.data_files_df.data_file_id.unique())
    client = ctx.obj["client"]
    _download_data_files(client, data_file_ids, data_file_dir)


@read_group.command(YoloWriter.format_name)
@click.argument("output_dir", type=str)
@CommonOptions.data_file_dir
@click.option(
    "--task",
    "-t",
    type=click.Choice([member.value for member in YoloWriter.TASK]),
    default=YoloWriter.TASK.DETECT,
)
@click.pass_context
def write_yolov8(ctx, output_dir, data_file_dir, task):
    image_cache_dir = Path(".") if data_file_dir is None else data_file_dir
    writer = YoloWriter(output_dir, image_cache_dir, task=task)

    combined_dataset = _combine_datasets(ctx)
    writer.write(combined_dataset)

    data_file_ids = list(combined_dataset.data_files_df.data_file_id.unique())
    client = ctx.obj["client"]
    _download_data_files(client, data_file_ids, data_file_dir)


dataset_group.add_command(read_group)
