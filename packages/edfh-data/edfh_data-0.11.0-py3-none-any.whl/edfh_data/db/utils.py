import datetime as dt
import os
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from sqlmodel import create_engine
from sqlmodel import SQLModel

if Path(".env").is_file():
    from dotenv import load_dotenv

    load_dotenv()


def db_connect_string():
    """Generate the DB connection string from different environment variables."""
    user = os.getenv("DB_USER", "dbuser")
    passwd = os.getenv("DB_PASSWD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", 3306)
    name = os.getenv("DB_NAME")

    return f"mysql+pymysql://{user}:{passwd}@{host}:{port}/{name}"


engine = create_engine(db_connect_string())


def init_db():
    SQLModel.metadata.create_all(engine)


def update_entry_fields(entry: SQLModel, update: Mapping) -> SQLModel:
    for field, value in update.items():
        if field in entry.__class__.model_fields:
            setattr(entry, field, value)
    return entry


def exclude_none(data: Mapping) -> dict:
    return {k: v for k, v in data.items() if v is not None}


def common_keys_equal(
    first: Mapping, second: Mapping, digits: int = 5, exclude_keys: Iterable = ()
) -> bool:
    """Compares the values of the common keys in two dictionaries. Returns True if all
    values are equal, False otherwise."""

    def equal(a, b):
        if isinstance(a, float) and isinstance(b, float):
            return round(a, digits) == round(b, digits)
        else:
            return a == b

    common_keys = set(first.keys()) & set(second.keys())
    return all(equal(first[k], second[k]) for k in common_keys - set(exclude_keys))


def index(items: Sequence, *, key: str) -> dict:
    """Returns a dictionary from a sequence of items with one of the items' field as
    key."""
    return {getattr(item, key): item for item in items}


def cycle_from_datetime(datetime: dt.datetime) -> int:
    """Return the powerplay cycle number corresponding to the speficied date."""
    cycle_1_start = dt.datetime.fromisoformat("2015-06-04T07:00:00+00:00")
    delta = datetime.replace(tzinfo=dt.timezone.utc) - cycle_1_start
    cycle = delta.total_seconds() / (7 * 24 * 3600) + 1

    return int(cycle)


def powerplay_state_updated(previous: Mapping, new: Mapping) -> bool:
    """Verify if powerplay state has changed."""
    # Replace null values with zeros
    reinf_prev = previous["powerplay_state_reinforcement"] or 0
    reinf_new = new["powerplay_state_reinforcement"] or 0
    underm_prev = previous["powerplay_state_undermining"] or 0
    underm_new = previous["powerplay_state_undermining"] or 0

    previous_cycle = cycle_from_datetime(previous["update_datetime"])
    new_cycle = cycle_from_datetime(new["update_datetime"])
    cycle_changed = new_cycle - previous_cycle > 0

    power_changed = new["controlling_power"] != previous["controlling_power"]
    state_changed = new["powerplay_state"] != previous["powerplay_state"]

    if cycle_changed:
        # Cycle changed, reinforcement & undermining may have decreased
        reinf_changed = reinf_new != reinf_prev
        underm_changed = underm_new != underm_prev
        return any([power_changed, state_changed, reinf_changed, underm_changed])
    else:
        # Cycle has not changed, reinforcement & undermining should only increase
        reinf_incr = reinf_new > reinf_prev
        underm_incr = underm_new > underm_prev
        return any([power_changed, state_changed, reinf_incr, underm_incr])
