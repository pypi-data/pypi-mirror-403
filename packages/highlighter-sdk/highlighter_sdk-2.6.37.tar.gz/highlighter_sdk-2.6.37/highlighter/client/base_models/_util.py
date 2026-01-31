from uuid import UUID, uuid4
from warnings import warn


def _get_uuid_str():
    return str(uuid4())


def _validate_uuid(v):
    if isinstance(v, UUID):
        return str(v)

    if v is None:
        if not hasattr(_validate_uuid, "_warned"):
            warn("entity_id was not provided, generating one")
            _validate_uuid._warned = True
        return _get_uuid_str()

    try:
        _ = UUID(v)
        return v
    except:  # noqa
        raise ValueError("Invalid UUID string")
