"""Pytest configuration and fixtures."""

import pytest
from typer.testing import CliRunner

from dblpcli.api import DBLPClient


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def client():
    """DBLP API client."""
    return DBLPClient(timeout=30.0)


# Sample XML responses for mocking

SAMPLE_PUBLICATION_SEARCH_XML = """<?xml version="1.0"?>
<result>
<query>transformer attention</query>
<status code="200">OK</status>
<time unit="msecs">50</time>
<completions total="0" computed="0" sent="0"/>
<hits total="1523" sent="2" first="0">
<hit score="5" id="123">
<info>
<url>https://dblp.org/rec/conf/nips/VaswaniSPUJGKP17</url>
<title>Attention is All You Need</title>
<year>2017</year>
<authors>
<author>Ashish Vaswani</author>
<author>Noam Shazeer</author>
<author>Niki Parmar</author>
</authors>
<venue>NeurIPS</venue>
<type>Conference and Workshop Papers</type>
<doi>10.5555/3295222.3295349</doi>
</info>
</hit>
<hit score="4" id="456">
<info>
<url>https://dblp.org/rec/journals/corr/abs-1706-03762</url>
<title>Attention Is All You Need</title>
<year>2017</year>
<authors>
<author>Ashish Vaswani</author>
<author>Noam Shazeer</author>
</authors>
<venue>CoRR</venue>
<type>Informal and Other Publications</type>
</info>
</hit>
</hits>
</result>
"""

SAMPLE_AUTHOR_SEARCH_XML = """<?xml version="1.0"?>
<result>
<query>Geoffrey Hinton</query>
<status code="200">OK</status>
<hits total="5" sent="2" first="0">
<hit score="10" id="789">
<info>
<url>https://dblp.org/pid/h/GeoffreyEHinton</url>
<author>Geoffrey E. Hinton</author>
<notes>
<note>University of Toronto</note>
<note>Google Brain</note>
</notes>
</info>
</hit>
<hit score="5" id="790">
<info>
<url>https://dblp.org/pid/123/4567</url>
<author>Geoffrey Hinton Jr.</author>
</info>
</hit>
</hits>
</result>
"""

SAMPLE_VENUE_SEARCH_XML = """<?xml version="1.0"?>
<result>
<query>NeurIPS</query>
<status code="200">OK</status>
<hits total="3" sent="2" first="0">
<hit score="10" id="v1">
<info>
<url>https://dblp.org/db/conf/nips/index.html</url>
<venue>Neural Information Processing Systems</venue>
<acronym>NeurIPS</acronym>
<type>Conference</type>
</info>
</hit>
<hit score="5" id="v2">
<info>
<url>https://dblp.org/db/conf/neurips/index.html</url>
<venue>NeurIPS Workshops</venue>
<acronym>NeurIPS-W</acronym>
<type>Conference</type>
</info>
</hit>
</hits>
</result>
"""

SAMPLE_PUBLICATION_XML = """<?xml version="1.0"?>
<dblp>
<inproceedings key="conf/nips/VaswaniSPUJGKP17" mdate="2023-01-01">
<title>Attention is All You Need</title>
<author>Ashish Vaswani</author>
<author>Noam Shazeer</author>
<author>Niki Parmar</author>
<author>Jakob Uszkoreit</author>
<author>Llion Jones</author>
<author>Aidan N. Gomez</author>
<author>Lukasz Kaiser</author>
<author>Illia Polosukhin</author>
<booktitle>NeurIPS</booktitle>
<year>2017</year>
<pages>5998-6008</pages>
<ee>https://doi.org/10.5555/3295222.3295349</ee>
</inproceedings>
</dblp>
"""

SAMPLE_AUTHOR_XML = """<?xml version="1.0"?>
<dblpperson name="Geoffrey E. Hinton" pid="h/GeoffreyEHinton" n="423">
<article key="journals/nature/HintonS06" mdate="2020-01-01">
<title>Reducing the Dimensionality of Data with Neural Networks</title>
<author>Geoffrey E. Hinton</author>
<author>Ruslan R. Salakhutdinov</author>
<journal>Science</journal>
<year>2006</year>
</article>
<inproceedings key="conf/nips/KrizhevskySH12" mdate="2020-01-01">
<title>ImageNet Classification with Deep Convolutional Neural Networks</title>
<author>Alex Krizhevsky</author>
<author>Ilya Sutskever</author>
<author>Geoffrey E. Hinton</author>
<booktitle>NeurIPS</booktitle>
<year>2012</year>
</inproceedings>
</dblpperson>
"""

SAMPLE_BIBTEX = """@inproceedings{DBLP:conf/nips/VaswaniSPUJGKP17,
  author       = {Ashish Vaswani and
                  Noam Shazeer and
                  Niki Parmar and
                  Jakob Uszkoreit and
                  Llion Jones and
                  Aidan N. Gomez and
                  Lukasz Kaiser and
                  Illia Polosukhin},
  title        = {Attention is All You Need},
  booktitle    = {NeurIPS},
  pages        = {5998--6008},
  year         = {2017},
}
"""


@pytest.fixture
def sample_publication_search_xml():
    return SAMPLE_PUBLICATION_SEARCH_XML


@pytest.fixture
def sample_author_search_xml():
    return SAMPLE_AUTHOR_SEARCH_XML


@pytest.fixture
def sample_venue_search_xml():
    return SAMPLE_VENUE_SEARCH_XML


@pytest.fixture
def sample_publication_xml():
    return SAMPLE_PUBLICATION_XML


@pytest.fixture
def sample_author_xml():
    return SAMPLE_AUTHOR_XML


@pytest.fixture
def sample_bibtex():
    return SAMPLE_BIBTEX
