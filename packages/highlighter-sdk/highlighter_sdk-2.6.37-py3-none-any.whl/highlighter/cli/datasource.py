"""CLI commands for data source management."""

from __future__ import annotations

import copy
import csv
import json
import os
import sys
import tempfile
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import List, Optional
from urllib.parse import urlparse
from uuid import UUID

import click
from tqdm import tqdm

from highlighter.cli.discovery_cli import (
    common_discovery_options,
    run_discovery,
)
from highlighter.client.base_models import PageInfo
from highlighter.client.io import (
    HL_DOWNLOAD_TIMEOUT,
    download_bytes,
)
from highlighter.core import GQLBaseModel
from highlighter.datasource.models import LocalDataSourceEntry, LocalDataSourceFile
from highlighter.datasource.service import DataSourceService
from highlighter.network.mdns import (
    DiscoveredDevice,
    DiscoveryError,
    normalize_mac,
)

DEFAULT_URI_PATTERN = "rtsp://{ip}:554/stream"
DEFAULT_NAME_PATTERN = "{service_name}"
MATCH_BY_CHOICES = [
    "id",
    "uuid",
    "name",
    "source_uri",
    "mac",
    "serial",
    "mac-address",
    "serial-number",
    "mac_address",
    "serial_number",
    "auto",
]


def normalize_match_by(match_by: str) -> str:
    match_by_aliases = {
        "mac-address": "mac",
        "mac_address": "mac",
        "serial-number": "serial",
        "serial_number": "serial",
    }
    return match_by_aliases.get(match_by, match_by)


MANIFEST_FIELDS = [
    "id",
    "uuid",
    "original_source_url",
    "filename",
    "file_hash",
    "file_size",
    "mime_type",
    "content_type",
    "width",
    "height",
    "duration",
    "recorded_at",
    "local_path",
    "download_status",
]
FAILED_SAMPLE_LIMIT = 10


class FilePresignedExtended(GQLBaseModel):
    id: str
    uuid: UUID
    original_source_url: str
    file_url_original: str
    filename: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    content_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    recorded_at: Optional[datetime] = None


class FileConnectionExtended(GQLBaseModel):
    page_info: PageInfo
    nodes: List[FilePresignedExtended]


@click.group("datasource")
@click.pass_context
def datasource_group(ctx):
    """Manage data sources for Highlighter."""
    pass


@datasource_group.group("discover")
@click.pass_context
def discover_group(ctx):
    """Commands for network device discovery and data source export."""
    pass


@discover_group.command("list")
@click.option(
    "--show-mac/--no-show-mac",
    default=True,
    help="Show MAC addresses (requires ARP access)",
)
@common_discovery_options
def list_devices(timeout, service_types, keywords, max_mac_workers, show_mac):
    """List all discovered devices on the network."""
    click.echo("Discovering devices on the network...")
    try:
        devices = run_discovery(
            timeout=timeout,
            resolve_macs=show_mac,
            service_types=service_types,
            keywords=keywords,
            max_mac_workers=max_mac_workers,
        )
    except DiscoveryError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    if not devices:
        click.echo("No devices found.")
        return

    click.echo(f"\nFound {len(devices)} device(s):\n")

    for i, device in enumerate(devices, 1):
        click.echo(f"{i}. {device.service_name}")
        click.echo(f"   IP:       {device.ip}:{device.port}")
        click.echo(f"   Hostname: {device.hostname}")
        if device.serial:
            click.echo(f"   Serial:   {device.serial}")
        if show_mac:
            mac = device.mac or "Unknown"
            click.echo(f"   MAC:      {mac}")
        click.echo()


@discover_group.command("find")
@click.option(
    "-m", "--mac", type=str, help="MAC address to search for (format: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)"
)
@click.option("-s", "--serial", type=str, help="Serial number to search for")
@common_discovery_options
def find_device(
    mac: Optional[str], serial: Optional[str], timeout: int, service_types, keywords, max_mac_workers
) -> None:
    """Find a device by MAC address or serial number."""
    if not mac and not serial:
        click.echo("Error: Must provide either --mac or --serial", err=True)
        sys.exit(1)

    normalized_mac = None
    if mac:
        normalized_mac = normalize_mac(mac)
        if not normalized_mac:
            click.echo(f"Error: Invalid MAC address format: {mac}", err=True)
            click.echo("Expected format: XX:XX:XX:XX:XX:XX", err=True)
            sys.exit(1)

    click.echo("Discovering devices on the network...")
    try:
        devices = run_discovery(
            timeout=timeout,
            resolve_macs=True,
            service_types=service_types,
            keywords=keywords,
            max_mac_workers=max_mac_workers,
        )
    except DiscoveryError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    if not devices:
        click.echo("No devices found.")
        sys.exit(1)

    matches: List[DiscoveredDevice] = []
    for device in devices:
        if normalized_mac and (device.mac or "").upper() == normalized_mac:
            matches.append(device)
        elif serial and device.serial and serial.upper() in device.serial.upper():
            matches.append(device)

    if not matches:
        if normalized_mac:
            click.echo(f"No device found with MAC address: {normalized_mac}", err=True)
        if serial:
            click.echo(f"No device found with serial number: {serial}", err=True)
        sys.exit(1)

    if len(matches) > 1:
        click.echo("Warning: Multiple devices match the criteria:", err=True)
        for device in matches:
            click.echo(
                f"  - {device.ip} (Serial: {device.serial or 'Unknown'}, MAC: {device.mac or 'Unknown'})",
                err=True,
            )
        click.echo()

    device = matches[0]
    click.echo("Found device:")
    click.echo(f"  Service:  {device.service_name}")
    click.echo(f"  IP:       {device.ip}")
    click.echo(f"  Port:     {device.port}")
    click.echo(f"  Hostname: {device.hostname}")
    if device.serial:
        click.echo(f"  Serial:   {device.serial}")
    click.echo(f"  MAC:      {device.mac or 'Unknown'}")

    click.echo(f"\nIP Address: {device.ip}")


@discover_group.command("batch")
@click.option(
    "-f",
    "--file",
    type=click.Path(exists=True, readable=True),
    help="File containing MAC addresses (one per line)",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Write lookup results to a file",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["csv", "datasource"]),
    default="csv",
    show_default=True,
    help="Output as CSV or datasource JSON (for cloud import)",
)
@click.option(
    "-T",
    "--template",
    type=str,
    help="Template name for datasource export (format=datasource)",
)
@click.option(
    "--uri-pattern",
    type=str,
    default=DEFAULT_URI_PATTERN,
    show_default=True,
    help="URI pattern for datasource export (format=datasource)",
)
@click.option(
    "--name-pattern",
    type=str,
    default=DEFAULT_NAME_PATTERN,
    show_default=True,
    help="Name pattern for datasource export (format=datasource)",
)
@click.option("--csv/--no-csv", default=True, help="Include CSV header (default: True)")
@click.option("--quiet/--no-quiet", default=False, help="Suppress discovery messages, only show results")
@click.option(
    "--show-hostname/--no-show-hostname", default=True, help="Include hostname in output (default: True)"
)
@click.argument("macs", nargs=-1)
@common_discovery_options
@click.pass_context
def batch_find(
    ctx,
    file,
    output,
    output_format,
    template,
    uri_pattern,
    name_pattern,
    timeout,
    csv,
    quiet,
    macs,
    service_types,
    keywords,
    max_mac_workers,
    show_hostname,
):
    """Find multiple devices by MAC addresses and emit results."""

    class MacRequest:
        def __init__(self, mac: str, name: Optional[str] = None) -> None:
            self.mac = mac
            self.name = name

    mac_list: List[str] = []

    if macs:
        mac_list.extend(macs)

    if file:
        with open(file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith("#"):
                    mac_list.append(line)

    if not sys.stdin.isatty() and not file and not macs:
        for line in sys.stdin:
            line = line.strip()
            if line and not line.startswith("#"):
                mac_list.append(line)

    if not mac_list:
        click.echo("Error: No MAC addresses provided for batch lookup", err=True)
        click.echo("Use --file, provide MACs as arguments, or pipe to stdin", err=True)
        sys.exit(1)

    mac_requests: List[MacRequest] = []
    for mac in mac_list:
        requested_name = None
        mac_value = mac
        if "=" in mac:
            parts = mac.split("=", 1)
            requested_name = parts[0].strip() or None
            mac_value = parts[1].strip()

        norm = normalize_mac(mac_value)
        if norm:
            mac_requests.append(MacRequest(norm, requested_name))
        else:
            if not quiet:
                click.echo(f"Warning: Invalid MAC address format: {mac}", err=True)

    if not mac_requests:
        click.echo("Error: No valid MAC addresses found", err=True)
        sys.exit(1)

    patterns_provided = uri_pattern != DEFAULT_URI_PATTERN or name_pattern != DEFAULT_NAME_PATTERN
    if output_format == "csv" and (template or patterns_provided):
        click.echo(
            "Error: --template/--uri-pattern/--name-pattern are only valid when --format=datasource",
            err=True,
        )
        sys.exit(1)

    if not quiet:
        click.echo(
            f"Discovering devices on the network (searching for {len(mac_requests)} MAC addresses)...",
            err=True,
        )

    try:
        devices = run_discovery(
            timeout=timeout,
            resolve_macs=True,
            service_types=service_types,
            keywords=keywords,
            max_mac_workers=max_mac_workers,
        )
    except DiscoveryError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    mac_to_device = {device.mac: device for device in devices if device.mac}

    found_count = 0
    if output_format == "datasource":
        # Validate template/pattern usage
        if template and patterns_provided:
            click.echo(
                "Error: Cannot specify both --template and custom patterns (--uri-pattern/--name-pattern)",
                err=True,
            )
            sys.exit(1)

        service = DataSourceService(ctx.obj["client"])
        loaded_template = None
        if template:
            loaded_template = service.load_template(template)
            if not loaded_template:
                click.echo(f"Error: Template '{template}' not found", err=True)
                available = service.list_templates()
                if available:
                    click.echo(f"Available templates: {', '.join(available)}", err=True)
                else:
                    click.echo("No templates available", err=True)
                sys.exit(1)

        entries = []
        seen_source_uris = set()
        for request in mac_requests:
            norm_mac = request.mac
            device = mac_to_device.get(norm_mac)
            if not device:
                continue
            if loaded_template:
                entry = service.apply_template(loaded_template, device, requested_name=request.name)
            else:
                placeholders = {
                    "ip": device.ip or "",
                    "hostname": device.hostname or "",
                    "port": device.port or "",
                    "serial": device.serial or "",
                    "mac": device.mac or "",
                    "service_name": device.service_name or "",
                }
                source_uri = uri_pattern.format(**placeholders)
                name = name_pattern.format(**placeholders)
                entry = LocalDataSourceEntry(
                    name=request.name or name,
                    source_uri=source_uri,
                    mac=device.mac,
                    serial=device.serial,
                    hostname=device.hostname,
                    ip=device.ip,
                    port=device.port,
                    template=None,
                )
            source_uri = entry.source_uri or ""
            if source_uri and source_uri in seen_source_uris:
                continue
            if source_uri:
                seen_source_uris.add(source_uri)
            entries.append(entry)
            found_count += 1

        data_source_file = LocalDataSourceFile(
            data_sources=entries,
            template=template if template else None,
        )

        if output:
            output_path = Path(output)
            service.save_file(output_path, data_source_file)
            if not quiet:
                click.echo(f"Saved data sources to {output_path}", err=True)
        else:
            click.echo(
                json.dumps(
                    data_source_file.model_dump(mode="json", exclude_none=False), indent=2, default=str
                )
            )

    else:
        output_lines: List[str] = []
        if csv:
            header = "MAC,IP,Hostname" if show_hostname else "MAC,IP"
            output_lines.append(header)

        for request in mac_requests:
            norm_mac = request.mac
            device = mac_to_device.get(norm_mac)
            ip = device.ip if device else "not_found"
            hostname = device.hostname if device else ""
            if device:
                found_count += 1

            if show_hostname:
                output_lines.append(f"{norm_mac},{ip},{hostname}")
            else:
                output_lines.append(f"{norm_mac},{ip}")

        if output:
            output_path = Path(output)
            output_path.write_text("\n".join(output_lines) + ("\n" if output_lines else ""), encoding="utf-8")
            if not quiet:
                click.echo(f"Wrote results to {output_path}", err=True)

        for line in output_lines:
            click.echo(line)

    if not quiet:
        click.echo(f"\nFound {found_count}/{len(mac_requests)} devices", err=True)


@datasource_group.command("list")
@click.option(
    "--file", "-f", type=click.Path(exists=True), help="Local file path (if not specified, queries cloud)"
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "csv", "stream"]),
    default="table",
    show_default=True,
    help="Output format",
)
@click.option(
    "--stream-template",
    type=click.Path(exists=True),
    help="Template JSON for stream definitions (used with --format=stream)",
)
@click.pass_context
def list_datasources(ctx, file: Optional[str], format: str, stream_template: Optional[str]):
    """List data sources from cloud or local file."""
    client = ctx.obj["client"]
    service = DataSourceService(client)

    if file:
        # Load from local file
        data_source_file = service.load_file(Path(file))
        sources = data_source_file.data_sources
        if format != "stream":
            click.echo(f"Data sources from {file}:")
    else:
        # Fetch from cloud
        cloud_sources = service.fetch_from_cloud()
        if format != "stream":
            click.echo(f"Data sources from cloud ({len(cloud_sources)} total):")

        if format == "json":
            output = [{"id": s.id, "uuid": str(s.uuid), "name": s.name} for s in cloud_sources]
            click.echo(json.dumps(output, indent=2))
            return
        elif format == "csv":
            click.echo("id,uuid,name")
            for s in cloud_sources:
                click.echo(f"{s.id},{s.uuid},{s.name}")
            return
        elif format == "stream":
            sources = cloud_sources
            # fall through to stream formatting
        else:
            # Table format
            if not cloud_sources:
                click.echo("No data sources found.")
                return

            click.echo()
            for i, s in enumerate(cloud_sources, 1):
                click.echo(f"{i}. {s.name}")
                click.echo(f"   ID:   {s.id}")
                click.echo(f"   UUID: {s.uuid}")
                click.echo()
            return

    # Local file formatting
    if format == "json":
        click.echo(json.dumps([s.model_dump(mode="json") for s in sources], indent=2, default=str))
    elif format == "csv":
        click.echo("id,uuid,name,source_uri,mac,serial")
        for s in sources:
            click.echo(
                f"{s.id or ''},{s.uuid or ''},{s.name},{s.source_uri or ''},{s.mac or ''},{s.serial or ''}"
            )
    elif format == "stream":
        # Build stream definitions from a template
        def _format_value(value, placeholders):
            if isinstance(value, str):
                return value.format(**placeholders)
            if isinstance(value, dict):
                return {k: _format_value(v, placeholders) for k, v in value.items()}
            if isinstance(value, list):
                return [_format_value(v, placeholders) for v in value]
            return value

        if stream_template:
            with open(stream_template, "r", encoding="utf-8") as f:
                template_obj = json.load(f)
        else:
            template_obj = {"data_sources": "({source_uri})", "subgraph_name": "{name}"}

        stream_defs = []
        for s in sources:
            placeholders = {
                "id": s.id or "",
                "uuid": str(s.uuid) if s.uuid else "",
                "name": s.name,
                "source_uri": getattr(s, "source_uri", None) or "",
                "mac": getattr(s, "mac", None) or "",
                "serial": getattr(s, "serial", None) or "",
                "hostname": getattr(s, "hostname", None) or "",
                "ip": getattr(s, "ip", None) or "",
                "port": getattr(s, "port", None) or "",
            }
            try:
                formatted = _format_value(copy.deepcopy(template_obj), placeholders)
            except KeyError as exc:
                click.echo(f"Error: Unknown placeholder in stream template: {exc}", err=True)
                sys.exit(1)
            stream_defs.append(formatted)

        click.echo(json.dumps(stream_defs, indent=2))
    else:
        # Table format
        if not sources:
            click.echo("No data sources found.")
            return

        click.echo()
        for i, s in enumerate(sources, 1):
            click.echo(f"{i}. {s.name}")
            if s.id:
                click.echo(f"   ID:         {s.id}")
            if s.uuid:
                click.echo(f"   UUID:       {s.uuid}")
            if s.source_uri:
                click.echo(f"   Source URI: {s.source_uri}")
            if s.mac:
                click.echo(f"   MAC:        {s.mac}")
            if s.serial:
                click.echo(f"   Serial:     {s.serial}")
            click.echo()


@datasource_group.command("view")
@click.option("--id", type=int, help="Data source ID")
@click.option("--uuid", type=str, help="Data source UUID")
@click.option("--name", "-n", type=str, help="Data source name")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
    help="Output format",
)
@click.pass_context
def view_datasource(ctx, id: Optional[int], uuid: Optional[str], name: Optional[str], format: str):
    """View details of a single data source."""
    client = ctx.obj["client"]
    service = DataSourceService(client)

    # Validate that exactly one identifier is provided
    identifiers = [id, uuid, name]
    if sum(x is not None for x in identifiers) != 1:
        click.echo("Error: Must provide exactly one of --id, --uuid, or --name", err=True)
        sys.exit(1)

    # Fetch the data source
    try:
        if id:
            source = service.get_by_id(id)
        elif uuid:
            source = service.get_by_uuid(UUID(uuid))
        elif name:
            source = service.get_by_name(name)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not source:
        click.echo("Error: Data source not found", err=True)
        sys.exit(1)

    # Output
    if format == "json":
        output = {"id": source.id, "uuid": str(source.uuid), "name": source.name}
        click.echo(json.dumps(output, indent=2))
    else:
        # Table format
        click.echo(f"Data Source: {source.name}")
        click.echo(f"ID:   {source.id}")
        click.echo(f"UUID: {source.uuid}")


def _normalize_source_path(original_source_url: str) -> Path:
    """Normalize a source path to a safe relative path."""
    parsed = urlparse(original_source_url)
    if parsed.scheme and parsed.netloc:
        combined = f"{parsed.netloc}/{parsed.path.lstrip('/')}"
    else:
        combined = parsed.path or original_source_url

    combined = combined.replace("\\", "/")
    path = PurePosixPath(combined)
    safe_parts = [part for part in path.parts if part not in ("", ".", "..", "/")]
    return Path(*safe_parts)


def _safe_filename(filename: Optional[str]) -> str:
    if not filename:
        return ""
    normalized = filename.replace("\\", "/")
    return PurePosixPath(normalized).name


def _file_suffix(file) -> str:
    if file.filename:
        suffix = Path(file.filename).suffix
        if suffix:
            return suffix
    return _normalize_source_path(file.original_source_url).suffix


def _get_data_source_folder_name(data_source_id: int, data_source_name: str) -> str:
    """Generate a safe folder name for the data source."""
    # Sanitize the data source name for use in filesystem
    safe_name = data_source_name.replace("/", "-").replace("\\", "-").replace(":", "-")
    return f"{data_source_id}-{safe_name}"


def _resolve_download_path(file, output_path: Path, structure: str, resume: bool) -> Path:
    """Resolve the download path for a file based on structure.

    Args:
        file: File object with metadata
        output_path: Base directory to save files (may include data source subfolder)
        structure: Directory structure ('flat', 'source-url', 'filename')
        resume: Whether to resume/skip existing files

    Returns:
        Full path where file should be saved
    """
    # Both 'uuid' and 'flat' use UUID-based naming in a flat directory
    if structure in ("uuid", "flat"):
        suffix = _file_suffix(file)
        return output_path / f"{file.uuid}{suffix}"

    if structure == "source-url":
        source_path = _normalize_source_path(file.original_source_url)
        source_name = source_path.name or _safe_filename(file.filename)
        if not source_name:
            source_name = f"{file.uuid}{_file_suffix(file)}"

        source_dir = source_path.parent if source_path.name else source_path
        if source_dir != Path("."):
            return output_path / source_dir / source_name
        return output_path / source_name

    if structure == "filename":
        safe_name = _safe_filename(file.filename)
        if safe_name:
            target_path = output_path / safe_name
            if target_path.exists() and not resume:
                stem = target_path.stem
                suffix = target_path.suffix
                target_path = output_path / f"{stem}_{file.uuid}{suffix}"
            return target_path
        return output_path / f"{file.uuid}{_file_suffix(file)}"

    raise ValueError(f"Unknown structure: {structure}")


def _iter_file_pages(client, chunk_size, data_source_id=None, data_source_uuid=None):
    kwargs = {}
    if data_source_id is not None:
        kwargs["dataSourceId"] = [data_source_id]
    if data_source_uuid is not None:
        kwargs["dataSourceUuid"] = [str(data_source_uuid)]

    after = None
    while True:
        if after:
            kwargs["after"] = after
        response = client.fileConnection(
            return_type=FileConnectionExtended,
            first=chunk_size,
            **kwargs,
        )
        yield response.nodes

        page_info = response.page_info
        if not page_info or not page_info.has_next_page:
            break
        after = page_info.end_cursor


def _download_files(
    files,
    output_path,
    structure,
    threads,
    resume,
    batch_size=None,
    progress=None,
    client=None,
):
    """Download files into the requested directory structure.

    Args:
        files: List of file objects with presigned URLs
        output_path: Directory to save files (can include data source subfolder)
        structure: Directory structure ('flat', 'source-url', 'filename')
        threads: Number of download threads
        resume: Skip existing files
        batch_size: Number of files to submit at once (None = all)
        progress: Optional tqdm progress bar (created if None)
        client: Optional HLClient for presigned URL refresh on failures

    Returns:
        Dict mapping file IDs to local paths (or None for failed downloads)
    """
    id_to_path = {}
    total_files = len(files)
    if total_files == 0:
        return id_to_path

    effective_batch_size = batch_size if batch_size and batch_size > 0 else total_files
    owns_progress = progress is None

    def download_single_file(file):
        try:
            target_path = _resolve_download_path(file, output_path, structure, resume)

            if target_path.exists() and resume:
                return {file.id: target_path, "_error": None}

            target_path.parent.mkdir(parents=True, exist_ok=True)
            download_bytes(
                file.file_url_original,
                save_path=target_path,
                check_cached=resume,
                timeout=HL_DOWNLOAD_TIMEOUT,
            )
            return {file.id: target_path, "_error": None}
        except Exception as e:
            return {file.id: None, "_error": str(e)}

    if owns_progress:
        progress = tqdm(total=total_files, desc="Downloading files")

    failed_files = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for i in range(0, total_files, effective_batch_size):
            batch = files[i : i + effective_batch_size]
            futures = {executor.submit(download_single_file, file): file for file in batch}
            for future in as_completed(futures):
                result = future.result()
                error = result.pop("_error", None)
                id_to_path.update(result)

                # Track failed downloads for potential retry
                file_id = list(result.keys())[0]
                if result[file_id] is None and error:
                    file = futures[future]
                    failed_files.append((file, error))

                progress.update(1)

    # Retry failed downloads with fresh presigned URLs if client is available
    if client and failed_files:
        _retry_failed_downloads(
            client,
            failed_files,
            id_to_path,
            output_path,
            structure,
            resume,
            threads,
            progress,
        )

    if owns_progress:
        progress.close()

    return id_to_path


def _retry_failed_downloads(
    client,
    failed_files,
    id_to_path,
    output_path,
    structure,
    resume,
    threads,
    progress,
):
    """Retry failed downloads with fresh presigned URLs.

    This addresses presigned URL expiry by refetching fresh URLs for files
    that failed to download, which may be due to expired presigned URLs.
    """
    from highlighter.client.presigned_url import get_presigned_urls

    # Check if failures might be due to expired URLs (403, 404, timeout)
    url_expiry_indicators = ["403", "404", "timeout", "Forbidden", "Not Found"]
    retry_candidates = [
        (file, error)
        for file, error in failed_files
        if any(indicator in error for indicator in url_expiry_indicators)
    ]

    if not retry_candidates:
        # No URL expiry indicators, just log warnings
        for file, error in failed_files:
            warnings.warn(f"Failed to download file {file.id}: {error}")
        return

    # Refetch presigned URLs for retry candidates
    file_ids = [file.id for file, _ in retry_candidates]

    try:
        # Fetch fresh presigned URLs
        fresh_urls_gen = get_presigned_urls(client, ids=file_ids, uuids=[])
        fresh_urls = {str(f.id): f for f in fresh_urls_gen}

        def retry_download(file_tuple):
            file, error = file_tuple
            try:
                # Get fresh URL
                fresh_file = fresh_urls.get(str(file.id))
                if not fresh_file:
                    return {file.id: None}

                target_path = _resolve_download_path(file, output_path, structure, resume)
                target_path.parent.mkdir(parents=True, exist_ok=True)

                download_bytes(
                    fresh_file.file_url_original,
                    save_path=target_path,
                    check_cached=resume,
                    timeout=HL_DOWNLOAD_TIMEOUT,
                )
                return {file.id: target_path}
            except Exception as e:
                warnings.warn(f"Retry failed for file {file.id}: {e}")
                return {file.id: None}

        # Retry downloads with fresh URLs
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(retry_download, file_tuple) for file_tuple in retry_candidates]
            for future in as_completed(futures):
                result = future.result()
                id_to_path.update(result)

    except Exception as e:
        warnings.warn(f"Failed to refetch presigned URLs for retry: {e}")
        # Log all failures
        for file, error in retry_candidates:
            warnings.warn(f"Failed to download file {file.id}: {error}")


def _build_manifest_entry(file, local_path, base_output_path):
    """Build a manifest entry with path relative to base_output_path."""
    if local_path:
        try:
            relative_path = local_path.relative_to(base_output_path)
        except ValueError:
            relative_path = Path(os.path.relpath(local_path, base_output_path))
    else:
        relative_path = None

    return {
        "id": file.id,
        "uuid": str(file.uuid),
        "original_source_url": file.original_source_url,
        "filename": file.filename,
        "file_hash": file.file_hash,
        "file_size": file.file_size,
        "mime_type": file.mime_type,
        "content_type": file.content_type,
        "width": file.width,
        "height": file.height,
        "duration": file.duration,
        "recorded_at": file.recorded_at.isoformat() if file.recorded_at else None,
        "local_path": str(relative_path) if relative_path else None,
        "download_status": "success" if local_path else "failed",
    }


class _ManifestWriter:
    def __init__(self, source, output_path, manifest_format, structure):
        self.source = source
        self.output_path = output_path
        self.manifest_format = manifest_format
        self.structure = structure
        self._csv_file = None
        self._csv_writer = None
        self._jsonl_file = None
        self._jsonl_path = None

        if manifest_format == "csv":
            manifest_file = output_path / "manifest.csv"
            self._csv_file = open(manifest_file, "w", newline="")
            self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=MANIFEST_FIELDS)
            self._csv_writer.writeheader()

        elif manifest_format == "json":
            self._jsonl_file = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                delete=False,
                dir=output_path,
                prefix=".manifest_entries_",
                suffix=".jsonl",
            )
            self._jsonl_path = Path(self._jsonl_file.name)

    def write_entry(self, file, local_path, base_output_path=None):
        # Use provided base_output_path or fall back to self.output_path
        output_path_for_relative = base_output_path if base_output_path else self.output_path
        entry = _build_manifest_entry(file, local_path, output_path_for_relative)
        if self.manifest_format == "csv":
            self._csv_writer.writerow(entry)
        elif self.manifest_format == "json":
            self._jsonl_file.write(json.dumps(entry) + "\n")

    def close(self, total_files):
        if self.manifest_format == "csv":
            if self._csv_file:
                self._csv_file.close()
                click.echo(f"Manifest written to {self.output_path / 'manifest.csv'}")
            return

        if self.manifest_format == "json":
            if self._jsonl_file:
                self._jsonl_file.close()

            manifest_file = self.output_path / "manifest.json"
            with open(manifest_file, "w") as out_f:
                out_f.write("{\n")
                out_f.write(f'  "data_source_id": {json.dumps(self.source.id)},\n')
                out_f.write(f'  "data_source_uuid": {json.dumps(str(self.source.uuid))},\n')
                out_f.write(f'  "data_source_name": {json.dumps(self.source.name)},\n')
                out_f.write(f'  "exported_at": {json.dumps(datetime.now().isoformat())},\n')
                out_f.write(f'  "total_files": {json.dumps(total_files)},\n')
                out_f.write(f'  "structure": {json.dumps(self.structure)},\n')
                out_f.write('  "files": [\n')

                if self._jsonl_path:
                    with open(self._jsonl_path, "r") as in_f:
                        for index, line in enumerate(in_f):
                            if index > 0:
                                out_f.write(",\n")
                            out_f.write(f"    {line.rstrip()}")

                out_f.write("\n  ]\n}\n")

            if self._jsonl_path:
                try:
                    os.remove(self._jsonl_path)
                except OSError:
                    pass

            click.echo(f"Manifest written to {manifest_file}")

    def abort(self):
        if self._csv_file:
            self._csv_file.close()
        if self._jsonl_file:
            self._jsonl_file.close()
        if self._jsonl_path:
            try:
                os.remove(self._jsonl_path)
            except OSError:
                pass


@datasource_group.command("create")
@click.option("--name", "-n", type=str, required=True, help="Data source name")
@click.option("--source-uri", "-u", type=str, help="Source URI (e.g., rtsp://hostname:554/stream)")
@click.option("--mac", "--mac-address", "mac", type=str, help="Device MAC address")
@click.option("--serial", "--serial-number", "serial", type=str, help="Device serial number")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
    help="Output format",
)
@click.pass_context
def create_datasource(
    ctx, name: str, source_uri: Optional[str], mac: Optional[str], serial: Optional[str], format: str
):
    """Create a single data source in the cloud."""
    client = ctx.obj["client"]
    service = DataSourceService(client)

    try:
        created = service.create(
            name=name,
            source_uri=source_uri,
            serial_number=serial,
            mac_address=mac,
        )
        click.echo(f"Created data source: {created.name}")

        if format == "json":
            output = {"id": created.id, "uuid": str(created.uuid), "name": created.name}
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"ID:   {created.id}")
            click.echo(f"UUID: {created.uuid}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@datasource_group.command("update")
@click.option("--id", type=int, help="Data source ID")
@click.option("--uuid", type=str, help="Data source UUID")
@click.option("--name", "-n", type=str, help="Data source name (for lookup) or new name")
@click.option("--source-uri", "-u", type=str, help="New source URI")
@click.option("--mac", "--mac-address", "mac", type=str, help="New MAC address")
@click.option("--serial", "--serial-number", "serial", type=str, help="New serial number")
@click.option("--new-name", type=str, help="New name (when using --id or --uuid for lookup)")
@click.pass_context
def update_datasource(
    ctx,
    id: Optional[int],
    uuid: Optional[str],
    name: Optional[str],
    source_uri: Optional[str],
    mac: Optional[str],
    serial: Optional[str],
    new_name: Optional[str],
):
    """Update an existing data source in the cloud."""
    client = ctx.obj["client"]
    service = DataSourceService(client)

    # Validate that exactly one identifier is provided
    identifiers = [id, uuid, name]
    if sum(x is not None for x in identifiers) != 1:
        click.echo("Error: Must provide exactly one of --id, --uuid, or --name for lookup", err=True)
        sys.exit(1)

    # If using name for lookup but also want to change the name
    if name and new_name:
        # Lookup by name first
        existing = service.get_by_name(name)
        if not existing:
            click.echo(f"Error: Data source '{name}' not found", err=True)
            sys.exit(1)
        id = existing.id
        name = new_name

    try:
        updated = service.update(
            data_source_id=id,
            data_source_uuid=UUID(uuid) if uuid else None,
            name=name or new_name,
            source_uri=source_uri,
            serial_number=serial,
            mac_address=mac,
        )
        click.echo(f"Updated data source: {updated.name}")
        click.echo(f"ID:   {updated.id}")
        click.echo(f"UUID: {updated.uuid}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@datasource_group.command("delete")
@click.option("--id", type=int, help="Data source ID")
@click.option("--uuid", type=str, help="Data source UUID")
@click.option("--name", "-n", type=str, help="Data source name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_datasource(ctx, id: Optional[int], uuid: Optional[str], name: Optional[str], yes: bool):
    """Delete a data source from the cloud."""
    client = ctx.obj["client"]
    service = DataSourceService(client)

    # Validate that exactly one identifier is provided
    identifiers = [id, uuid, name]
    if sum(x is not None for x in identifiers) != 1:
        click.echo("Error: Must provide exactly one of --id, --uuid, or --name", err=True)
        sys.exit(1)

    # Lookup by name if needed
    if name:
        source = service.get_by_name(name)
        if not source:
            click.echo(f"Error: Data source '{name}' not found", err=True)
            sys.exit(1)
        id = source.id
        display_name = name
    else:
        # Fetch to show what we're deleting
        if id:
            source = service.get_by_id(id)
        else:
            source = service.get_by_uuid(UUID(uuid))

        if not source:
            click.echo("Error: Data source not found", err=True)
            sys.exit(1)
        display_name = source.name

    # Confirm deletion
    if not yes:
        confirm = click.confirm(f"Are you sure you want to delete data source '{display_name}'?")
        if not confirm:
            click.echo("Aborted.")
            return

    try:
        service.destroy(data_source_id=id, data_source_uuid=UUID(uuid) if uuid else None)
        click.echo(f"Deleted data source: {display_name}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@datasource_group.command("export")
@click.option("--id", type=int, help="Data source ID")
@click.option("--uuid", type=str, help="Data source UUID")
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(exists=False, file_okay=False),
    required=True,
    help="Output directory for downloaded files",
)
@click.option(
    "--structure",
    type=click.Choice(["flat", "source-url", "filename"]),
    default="source-url",
    show_default=True,
    help="Directory structure within {id}-{name} folder: flat (all files flat, named by UUID), source-url (organized by original_source_url path), filename (use original filename)",
)
@click.option(
    "--manifest",
    type=click.Choice(["json", "csv", "none"]),
    default="json",
    show_default=True,
    help="Generate manifest file with metadata",
)
@click.option(
    "--threads",
    type=int,
    default=8,
    show_default=True,
    help="Number of download threads",
)
@click.option(
    "--chunk-size",
    type=int,
    default=20,
    show_default=True,
    help="Number of files to query per GraphQL request",
)
@click.option(
    "--resume/--no-resume",
    default=True,
    show_default=True,
    help="Skip files that already exist (resume interrupted downloads)",
)
@click.pass_context
def export_datasource(ctx, id, uuid, output_dir, structure, manifest, threads, chunk_size, resume):
    """Download all files from a data source to local directory."""

    try:
        manifest_writer = None
        # Validate exactly one identifier
        identifiers = [id, uuid]
        if sum(x is not None for x in identifiers) != 1:
            click.echo("Error: Must provide exactly one of --id or --uuid", err=True)
            sys.exit(1)

        # Get client and service
        client = ctx.obj["client"]
        service = DataSourceService(client)

        # Verify data source exists (fail fast)
        if id:
            source = service.get_by_id(id)
        elif uuid:
            source = service.get_by_uuid(UUID(uuid))

        if not source:
            click.echo("Error: Data source not found", err=True)
            sys.exit(1)

        click.echo(f"Found data source: {source.name} (ID: {source.id}, UUID: {source.uuid})")

        # Query and stream files for this data source
        click.echo("Querying files...")

        # Create output directory with data source subfolder
        try:
            base_output_path = Path(output_dir)
            base_output_path.mkdir(parents=True, exist_ok=True)

            # Create data source subfolder
            ds_folder_name = _get_data_source_folder_name(source.id, source.name)
            output_path = base_output_path / ds_folder_name
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            click.echo(f"Error: Cannot create output directory: {e}", err=True)
            sys.exit(1)

        if manifest != "none":
            manifest_writer = _ManifestWriter(source, base_output_path, manifest, structure)

        click.echo("Downloading files...")
        total_files = 0
        successful = 0
        failed = 0
        failed_samples = []
        download_batch_size = chunk_size if chunk_size and chunk_size > 0 else None
        progress = tqdm(desc="Downloading files")

        try:
            for page in _iter_file_pages(
                client,
                chunk_size,
                data_source_id=id,
                data_source_uuid=uuid,
            ):
                if not page:
                    continue

                id_to_path = _download_files(
                    page,
                    output_path,
                    structure,
                    threads,
                    resume,
                    batch_size=download_batch_size,
                    progress=progress,
                    client=client,
                )

                for file in page:
                    local_path = id_to_path.get(file.id)
                    total_files += 1
                    if local_path:
                        successful += 1
                    else:
                        failed += 1
                        if len(failed_samples) < FAILED_SAMPLE_LIMIT:
                            failed_samples.append(file)
                    if manifest_writer:
                        manifest_writer.write_entry(file, local_path, base_output_path)
        finally:
            progress.close()

        if total_files == 0:
            click.echo("Warning: No files found in this data source", err=True)
            if manifest_writer:
                manifest_writer.close(total_files=0)
            sys.exit(0)

        if manifest_writer:
            manifest_writer.close(total_files=total_files)

        # Report results
        if failed > 0:
            click.echo(f"\nDownloaded {successful} files ({failed} failed)", err=True)
            if failed_samples:
                click.echo("\nFailed files:", err=True)
                for file in failed_samples:
                    click.echo(f"  - {file.id}: {file.original_source_url}", err=True)
                if failed > len(failed_samples):
                    click.echo(f"  ... and {failed - len(failed_samples)} more", err=True)
        else:
            click.echo(f"\nSuccessfully downloaded {successful} files")

    except Exception as e:
        if manifest_writer:
            manifest_writer.abort()
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@datasource_group.command("sync")
@click.option("--input", "-i", type=click.Path(exists=True), required=True, help="Input data sources file")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (if not specified, updates input file in-place)",
)
@click.option(
    "--match-by",
    type=click.Choice(MATCH_BY_CHOICES),
    default="auto",
    show_default=True,
    help="Matching strategy (supports mac/serial; use source_uri to skip duplicate URIs, use uuid to allow duplicates)",
)
@click.option("--dry-run", is_flag=True, help="Preview matches without writing output")
@click.pass_context
def sync_datasources(
    ctx,
    input: str,
    output: Optional[str],
    match_by: str,
    dry_run: bool,
):
    """Align a local datasources file with what's already in cloud.

    This does NOT create or update anything in the cloud. It only fetches
    cloud data sources, matches them to local entries, and writes matched
    cloud IDs/UUIDs back into the local file.
    """
    client = ctx.obj["client"]
    service = DataSourceService(client)
    match_by = normalize_match_by(match_by)

    input_path = Path(input)
    output_path = Path(output) if output else input_path

    # Load local file
    data_source_file = service.load_file(input_path)
    click.echo(f"Loaded {len(data_source_file.data_sources)} data sources from {input_path}")

    # Fetch cloud data sources
    click.echo("Fetching data sources from cloud...")
    cloud_sources = service.fetch_from_cloud()
    click.echo(f"Found {len(cloud_sources)} data sources in cloud")

    # Match entries
    matches = service.match_entries(data_source_file.data_sources, cloud_sources, match_by)

    # Display results
    matched_count = sum(1 for m in matches if m.is_matched)
    unmatched_count = len(matches) - matched_count

    click.echo(f"\nMatching results:")
    click.echo(f"  Matched:   {matched_count}")
    click.echo(f"  Unmatched: {unmatched_count}")

    if dry_run:
        click.echo("\nDry run - showing matches:")
        for match in matches:
            if match.is_matched:
                click.echo(
                    f"  ✓ {match.local.name} -> Cloud ID: {match.cloud.id} (matched by {match.match_type})"
                )
            else:
                click.echo(f"  ✗ {match.local.name} (no match)")
        return

    # Update local entries with cloud IDs
    for match in matches:
        if match.is_matched:
            match.local.id = match.cloud.id
            match.local.uuid = match.cloud.uuid

    # Save updated file
    service.save_file(output_path, data_source_file)
    click.echo(f"\nSaved updated data sources to {output_path}")


@datasource_group.command("import")
@click.option("--input", "-i", type=click.Path(exists=True), required=True, help="Input data sources file")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file with updated cloud IDs (if not specified, updates input in-place)",
)
@click.option(
    "--match-by",
    type=click.Choice(MATCH_BY_CHOICES),
    default="auto",
    show_default=True,
    help="Matching strategy for existing data sources (supports mac/serial; source_uri skips duplicates, uuid allows duplicates)",
)
@click.option("--dry-run", is_flag=True, help="Preview changes without applying them")
@click.pass_context
def import_datasources(
    ctx,
    input: str,
    output: Optional[str],
    match_by: str,
    dry_run: bool,
):
    """Push a local datasources file into the cloud.

    Upserts entries in the cloud, writing back cloud IDs/UUIDs to the file
    after applying changes.

    Input file format (JSON):
      {
        "data_sources": [
          {
            "name": "Camera 1",
            "source_uri": "rtsp://192.168.1.100:554/stream",
            "mac": "AA:BB:CC:DD:EE:FF",
            "serial": "SN-12345"
          }
        ],
        "template": "rtsp_camera",
        "metadata": {
          "created_at": "2025-01-01T00:00:00",
          "updated_at": "2025-01-01T00:00:00"
        }
      }
    """
    client = ctx.obj["client"]
    service = DataSourceService(client)
    match_by = normalize_match_by(match_by)

    input_path = Path(input)
    output_path = Path(output) if output else input_path

    # Load local file
    data_source_file = service.load_file(input_path)
    click.echo(f"Loaded {len(data_source_file.data_sources)} data sources from {input_path}")

    if dry_run:
        # Fetch cloud data sources for preview
        click.echo("Fetching data sources from cloud...")
        cloud_sources = service.fetch_from_cloud()
        matches = service.match_entries(data_source_file.data_sources, cloud_sources, match_by)

        click.echo("\nDry run - preview of actions:")
        for match in matches:
            if match.is_matched:
                click.echo(f"  UPDATE: {match.local.name} (ID: {match.cloud.id})")
            else:
                click.echo(f"  CREATE: {match.local.name}")
        return

    # Perform import
    click.echo("Importing data sources to cloud...")
    updated_entries, result = service.import_to_cloud(
        data_source_file.data_sources,
        create_missing=True,
        update_existing=True,
        match_by=match_by,
    )

    # Display results
    click.echo(f"\nImport results:")
    click.echo(f"  Matched:  {result.matched}")
    click.echo(f"  Created:  {result.created}")
    click.echo(f"  Updated:  {result.updated}")
    if result.skipped_duplicates:
        click.echo(f"  Skipped (duplicate source_uri): {result.skipped_duplicates}")
    click.echo(f"  Failed:   {result.failed}")

    if result.skipped_reasons:
        click.echo("\nSkipped:")
        for reason in result.skipped_reasons:
            click.echo(f"  - {reason}")

    if result.errors:
        click.echo("\nErrors:")
        for error in result.errors:
            click.echo(f"  - {error}", err=True)

    # Update file with new entries
    data_source_file.data_sources = updated_entries
    service.save_file(output_path, data_source_file)
    click.echo(f"\nSaved updated data sources to {output_path}")

    # Exit with error code if there were any failures
    if result.failed > 0 or result.errors:
        sys.exit(1)


@datasource_group.group("template")
def template_group():
    """Manage data source templates."""
    pass


@template_group.command("list")
@click.pass_context
def list_templates(ctx):
    """List available templates."""
    client = ctx.obj["client"]
    service = DataSourceService(client)

    templates = service.list_templates()

    if not templates:
        click.echo("No templates found.")
        return

    click.echo(f"Available templates ({len(templates)}):")
    for t in templates:
        click.echo(f"  - {t}")


@template_group.command("show")
@click.argument("template_name")
@click.pass_context
def show_template(ctx, template_name: str):
    """Show details of a template."""
    client = ctx.obj["client"]
    service = DataSourceService(client)

    template = service.load_template(template_name)

    if not template:
        click.echo(f"Error: Template '{template_name}' not found", err=True)
        sys.exit(1)

    click.echo(f"Template: {template.name}")
    click.echo(f"Description: {template.description}")
    click.echo(f"URI Pattern: {template.source_uri_pattern}")
    if template.default_port:
        click.echo(f"Default Port: {template.default_port}")
    if template.default_path:
        click.echo(f"Default Path: {template.default_path}")
