import errno as errno_module
import re
from typing import Any, Dict, Optional


def format_ffmpeg_error_message(operation_name: str, error: Exception, source: object) -> str:
    details = extract_ffmpeg_error_details(error)
    reason = details.get("strerror") or details.get("message") or "Unknown FFmpeg error"
    if "last error log:" in reason:
        reason = reason.split("last error log:", 1)[0].strip().rstrip(";")

    parts = [f"RETRY: {operation_name} failed with FFmpeg error: {reason}"]
    errno_val = details.get("errno")
    if errno_val is not None:
        errno_name = details.get("errno_name")
        if errno_name:
            parts.append(f"errno={errno_val}({errno_name})")
        else:
            parts.append(f"errno={errno_val}")
    if details.get("ffmpeg_log"):
        parts.append(f"ffmpeg_log={details['ffmpeg_log']}")
    if details.get("hint"):
        parts.append(f"hint={details['hint']}")
    parts.append(f"Source: {source}")
    return " | ".join(parts)


def extract_ffmpeg_error_details(error: Exception) -> Dict[str, Any]:
    message = str(error)
    details: Dict[str, Any] = {"message": message}
    errno_val = getattr(error, "errno", None)
    if errno_val is not None:
        details["errno"] = errno_val
        details["errno_name"] = errno_module.errorcode.get(errno_val)
        details["strerror"] = getattr(error, "strerror", None)

    last_log = None
    error_log = getattr(error, "log", None)
    if error_log:
        try:
            last_log = error_log[-1]
        except Exception:
            last_log = None
        if last_log is not None and not isinstance(last_log, str):
            last_log = str(last_log)
    if not last_log:
        match = re.search(r"last error log:\s*(.+)$", message)
        if match:
            last_log = match.group(1).strip()
    if last_log:
        details["ffmpeg_log"] = last_log

    details["hint"] = ffmpeg_error_hint(
        message=message,
        last_log=details.get("ffmpeg_log"),
        errno_name=details.get("errno_name"),
        errno_val=details.get("errno"),
    )
    return details


def ffmpeg_error_hint(
    message: str,
    last_log: Optional[str],
    errno_name: Optional[str],
    errno_val: Optional[int],
) -> Optional[str]:
    combined = f"{message} {last_log or ''}".lower()

    if "time_scale/num_units_in_tick" in combined:
        return "H.264 timing metadata is invalid; check camera/encoder firmware or stream settings."
    if "invalid data found when processing input" in combined:
        return "Stream data looks corrupted or codec parameters mismatch; check encoder output."
    if "connection reset" in combined or errno_name in {"ECONNRESET", "ECONNREFUSED", "ETIMEDOUT"}:
        return "Network interruption from source; check camera/network stability."
    if errno_name in {"EIO", "ENETDOWN", "ENETUNREACH", "EHOSTUNREACH"} or errno_val in {
        errno_module.EIO,
        errno_module.ENETDOWN,
        errno_module.ENETUNREACH,
        errno_module.EHOSTUNREACH,
    }:
        return "I/O error while reading the stream; often network or camera instability."
    if "end of file" in combined:
        return "Source ended or closed the stream."

    return None
