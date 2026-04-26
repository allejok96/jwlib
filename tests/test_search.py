import logging
import jwlib.search as jw


def test_search_default(caplog) -> None:
    caplog.set_level(logging.DEBUG)

    page = jw.search('Caleb')
    assert 'opening: https://b.jw-cdn.org/apis/search/results/E/all/?q=Caleb' in caplog.messages
    caplog.clear()

    assert isinstance(page.layout, list)
    assert page.insight  # TODO
    assert page.pagination
    assert page.pagination_label

    insight = page.insight
    assert insight.filter == jw.FILTER_ALL
    assert insight.offset == 0
    assert insight.page == 1
    assert insight.query == 'Caleb'
    assert insight.sort == jw.SORT_RELATIVITY
    assert insight.total > 100
    assert insight.total_relation == 'eq'

    # Check filtering links
    assert sum(1 for f in page.filters if f.selected)
    filter_link = next(f for f in page.filters if not f.selected and jw.FILTER_VIDEO in f.url)
    filter_page = filter_link.open()
    assert 'opening: https://b.jw-cdn.org/apis/search/results/E/videos?q=Caleb' in caplog.messages
    caplog.clear()
    assert filter_page.insight.filter != insight.filter
    assert filter_page.insight.total < insight.total

    # If there's no groups, this should make a dummy group
    assert len(filter_page.result_groups) == 1

    deep = next(r.deep_links[0] for r in filter_page.results if r.deep_links)

    assert isinstance(deep.title, str)
    assert deep.label
    assert deep.lank
    assert deep.rank > -1
    assert deep.snippet
    assert deep.urls
    assert deep.url_jw

    # Check sorting links
    assert sum(1 for s in page.sorts if s.selected)
    sort_link = next(s for s in page.sorts if not s.selected and jw.SORT_NEWEST in s.url)
    sort_page = sort_link.open()
    assert 'opening: https://b.jw-cdn.org/apis/search/results/E/all?sort=newest&q=Caleb' in caplog.messages
    caplog.clear()
    assert sort_page.insight.sort != insight.sort
    # sometimes the sorting order changes the total
    # assert sort_page.insight.total == insight.total

    # Check pagination links
    assert page.first is not None and page.first.selected
    assert page.last is not None
    assert page.next is not None
    assert page.previous is None
    last_page = page.last.open()
    assert last_page.first is not None
    # sometimes the last page turns out to not be the last page
    # assert last_page.last.selected
    assert last_page.last is not None
    # assert last_page.next is None
    assert last_page.previous is not None
    assert last_page.insight.offset > 0
    assert last_page.insight.page > 1

    # Check results
    results = page.results
    assert any(r.context for r in results)
    assert any(r.duration for r in results)
    assert any(r.image for r in results)
    assert all(r.key for r in results)
    assert any(r.snippet for r in results)
    assert all(r.title for r in results)
    assert all(r.type for r in results)
    assert all(r.urls for r in results)
    assert any(r.url_jw for r in results)
    assert any(r.url_wol for r in results)

    # When searching "Caleb" there should be at least three types of results: audio, video and publications
    assert len(set(r.type for r in results)) >= 3

    groups = page.result_groups

    # This should be true for groups too
    assert len(set(r.type for g in groups for r in g.results)) >= 3

    # All results in a group should have the same subtype
    for g in groups:
        assert len(set(r.type for r in g.results)) == 1

    assert any(g.label for g in groups)
    assert any(g.layout for g in groups)
    assert any(g.links for g in groups)


def test_search_parameters() -> None:
    page = jw.search('Kevin', filter_type=jw.FILTER_AUDIO, language='Z', sort=jw.SORT_NEWEST)
    assert page.insight.total > 5
    assert page.insight.filter == jw.FILTER_AUDIO
    assert page.insight.sort == jw.SORT_NEWEST


def test_invalid_search() -> None:
    page = jw.search('vedermödan', filter_type=jw.FILTER_VIDEO)
    assert len(page.results) == 0
    assert any(page.messages)
