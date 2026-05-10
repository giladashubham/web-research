from webresearch.sources.registry import SourceRegistry
from webresearch.types import FetchStatus, SourceInput


def test_same_normalized_url_returns_same_record():
    registry = SourceRegistry()

    first = registry.add(
        SourceInput(url="https://example.com/report/?utm_source=newsletter#top")
    )
    second = registry.add(SourceInput(url="https://EXAMPLE.com/report"))

    assert second == first
    assert registry.list() == (first,)


def test_first_writer_wins_for_title_and_publisher():
    registry = SourceRegistry()

    first = registry.add(
        SourceInput(
            url="https://example.com/report", title="Original", publisher="Example"
        )
    )
    second = registry.add(
        SourceInput(
            url="https://example.com/report/", title="Updated", publisher="Other"
        )
    )

    assert second is first
    assert second.title == "Original"
    assert second.publisher == "Example"


def test_source_ids_are_stable_and_sequential_per_registry():
    registry = SourceRegistry()
    other_registry = SourceRegistry()

    first = registry.add(SourceInput(url="https://example.com/a"))
    second = registry.add(SourceInput(url="https://example.com/b"))
    other_first = other_registry.add(SourceInput(url="https://example.com/a"))

    assert first.id == "src_1"
    assert second.id == "src_2"
    assert other_first.id == "src_1"
    assert registry.get("src_1") is first
    assert registry.get_by_url("https://example.com/a/") is first
    assert registry.list() == (first, second)


def test_mark_fetch_status_updates_status_without_losing_fields():
    registry = SourceRegistry()
    record = registry.add(
        SourceInput(
            url="https://example.com/report", title="Report", publisher="Example"
        )
    )

    registry.mark_fetch_status(record.id, FetchStatus.FETCHED)

    updated = registry.get(record.id)
    assert updated is record
    assert updated.fetch_status == FetchStatus.FETCHED
    assert updated.title == "Report"
    assert updated.publisher == "Example"


def test_source_added_callback_fires_once_for_first_registration():
    added: list[str] = []
    registry = SourceRegistry(source_added=lambda source: added.append(source.id))

    registry.add(SourceInput(url="https://example.com/report?utm_campaign=x"))
    registry.add(SourceInput(url="https://example.com/report"))

    assert added == ["src_1"]
