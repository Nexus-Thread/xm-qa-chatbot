"""Unit tests for stream-project registry invariants and lookups."""

import pytest

from qa_chatbot.domain import BusinessStream, Project, StreamId, StreamProjectRegistry
from qa_chatbot.domain.exceptions import InvalidConfigurationError


def _stream(stream_id: str, *, name: str, order: int = 0) -> BusinessStream:
    """Create a stream helper for registry tests."""
    return BusinessStream(id=StreamId(stream_id), name=name, order=order)


def _project(project_id: str, *, name: str, stream_id: str) -> Project:
    """Create a project helper for registry tests."""
    return Project(id=project_id, name=name, business_stream_id=StreamId(stream_id))


def test_registry_rejects_duplicate_stream_ids() -> None:
    """Reject registry construction when stream identifiers are duplicated."""
    first = _stream("stream-a", name="Stream A")
    duplicate = _stream("stream-a", name="Stream A Duplicate", order=1)
    project = _project("project-a", name="Project A", stream_id="stream-a")

    with pytest.raises(InvalidConfigurationError, match="Business stream IDs must be unique"):
        StreamProjectRegistry(streams=(first, duplicate), projects=(project,))


def test_registry_rejects_duplicate_project_ids() -> None:
    """Reject registry construction when project identifiers are duplicated."""
    stream = _stream("stream-a", name="Stream A")
    first = _project("project-a", name="Project A", stream_id="stream-a")
    duplicate = _project("project-a", name="Project A Duplicate", stream_id="stream-a")

    with pytest.raises(InvalidConfigurationError, match="Project IDs must be unique"):
        StreamProjectRegistry(streams=(stream,), projects=(first, duplicate))


def test_registry_rejects_projects_referencing_unknown_streams() -> None:
    """Reject registry construction when a project points to an unknown stream."""
    stream = _stream("stream-a", name="Stream A")
    project = _project("project-a", name="Project A", stream_id="stream-b")

    with pytest.raises(InvalidConfigurationError, match="references unknown stream"):
        StreamProjectRegistry(streams=(stream,), projects=(project,))


def test_projects_for_stream_filters_projects_by_stream_id() -> None:
    """Return only projects that belong to the requested stream."""
    stream_a = _stream("stream-a", name="Stream A")
    stream_b = _stream("stream-b", name="Stream B", order=1)
    project_a = _project("project-a", name="Project A", stream_id="stream-a")
    project_b = _project("project-b", name="Project B", stream_id="stream-b")
    registry = StreamProjectRegistry(streams=(stream_a, stream_b), projects=(project_a, project_b))

    projects = registry.projects_for_stream(StreamId("stream-a"))

    assert projects == (project_a,)


def test_stream_name_raises_for_unknown_stream_id() -> None:
    """Raise a configuration error when stream name lookup misses."""
    stream = _stream("stream-a", name="Stream A")
    project = _project("project-a", name="Project A", stream_id="stream-a")
    registry = StreamProjectRegistry(streams=(stream,), projects=(project,))

    with pytest.raises(InvalidConfigurationError, match="Unknown stream id stream-missing"):
        registry.stream_name(StreamId("stream-missing"))
