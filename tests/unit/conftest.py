import os
import pytest
import datetime
import requests
import json
from lxml import html
from findpapers.models.publication import Publication
from findpapers.models.paper import Paper
from findpapers.models.search import Search
from findpapers.models.bibliometrics import AcmBibliometrics, ScopusBibliometrics
import findpapers.searcher.scopus_searcher as scopus_searcher


@pytest.fixture
def acm_bibliometrics():
    return AcmBibliometrics(2.2, 4.7)


@pytest.fixture
def scopus_bibliometrics():
    return ScopusBibliometrics(3.5, 7.5, 1.0)


@pytest.fixture
def publication():
    return Publication('awesome publication title', 'isbn-X', 'issn-X', 'that publisher', 'Journal')


@pytest.fixture
def paper(publication):
    authors = {'Dr Paul', 'Dr John', 'Dr George', 'Dr Ringo'}
    publication_date = datetime.date(1969, 1, 30)
    paper_url = "https://en.wikipedia.org/wiki/The_Beatles'_rooftop_concert"
    urls = {paper_url}

    return Paper('awesome paper title', 'a long abstract', authors, publication, publication_date, urls)


@pytest.fixture
def search():
    return Search('this AND that', datetime.date(1969, 1, 30), ['humanities', 'economics'], 2)


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.delattr("requests.sessions.Session.request")


def prevent_search_results_infinite_loop(search_results):
    # creating fake paper titles for next recursion
    for i, entry in enumerate(search_results.get('entry')):
        entry['dc:title'] = f'FAKE PAPER TITLE {i}'

    search_results['link'] = []  # preventing infinite recursion


@pytest.fixture
def mock_scopus_get_search_results(monkeypatch):

    def mocked_search_results(*args, **kwargs):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, '../data/scopus-api-search.json')
        search_results = json.load(open(filename)).get('search-results')

        # if it's a recursive call for new search results
        if len(args) > 0 and args[1] is not None:
            prevent_search_results_infinite_loop(search_results)

        return search_results

    monkeypatch.setattr(
        scopus_searcher, 'get_search_results', mocked_search_results)


@pytest.fixture
def mock_scopus_get_search_results_entry_error(monkeypatch):

    def mocked_search_results(*args, **kwargs):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, '../data/scopus-api-search.json')
        search_results = json.load(open(filename))['search-results']

        # removing the title value from the first paper
        del search_results.get('entry')[0]['dc:title']

        # if it's a recursive call for new search results
        if len(args) > 0 and args[1] is not None:
            prevent_search_results_infinite_loop(search_results)

        return search_results

    monkeypatch.setattr(
        scopus_searcher, 'get_search_results', mocked_search_results)


@pytest.fixture
def mock_scopus_get_publication_entry(monkeypatch):

    def mocked_publication_entry(*args, **kwargs):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, '../data/scopus-api-publication.json')
        return json.load(open(filename))['serial-metadata-response']['entry'][0]

    monkeypatch.setattr(
        scopus_searcher, 'get_publication_entry', mocked_publication_entry)


@pytest.fixture
def mock_scopus_get_paper_page(monkeypatch):

    def mocked_paper_page(*args, **kwargs):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, '../data/scopus-paper-page.html')
        with open(filename) as f:
            page = f.read()
        return html.fromstring(page)

    monkeypatch.setattr(scopus_searcher, 'get_paper_page', mocked_paper_page)


@pytest.fixture
def mock_scopus_get_paper_page_error(monkeypatch):

    def mocked_paper_page(*args, **kwargs):
        raise RuntimeError()

    monkeypatch.setattr(scopus_searcher, 'get_paper_page', mocked_paper_page)
