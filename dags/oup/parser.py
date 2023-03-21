import xml.etree.ElementTree as ET

from common.parsing.parser import IParser
from common.parsing.xml_extractors import AttributeExtractor, CustomExtractor
from common.utils import get_text_value
from structlog import get_logger


class OUPParser(IParser):
    def __init__(self) -> None:
        self.logger = get_logger().bind(class_name=type(self).__name__)
        self.article_type_mapping = {
            "research-article": "article",
            "corrected-article": "article",
            "original-article": "article",
            "correction": "corrigendum",
            "addendum": "addendum",
            "editorial": "editorial",
        }

        extractors = [
            CustomExtractor(
                destination="dois", extraction_function=self._get_dois, required=True
            ),
            AttributeExtractor(
                destination="page_nr",
                source="front/article-meta/counts/page-count",
                attribute="count",
                extra_function=lambda x: int(x),
            ),
            CustomExtractor(
                destination="journal_doctype",
                extraction_function=self._get_journal_doctype,
            ),
            CustomExtractor(
                destination="arxiv_eprints",
                extraction_function=self._get_arxiv_eprints,
            ),
            CustomExtractor(
                destination="authors",
                extraction_function=self._get_authors,
                required=True,
            ),
        ]
        super().__init__(extractors)

    def _get_dois(self, article: ET.Element):
        source = ".front/article-meta/article-id/[@pub-id-type='doi']"
        doi_element = article.find(source)
        doi = get_text_value(doi_element)
        if not doi:
            return []
        self.logger.msg("Parsing dois for article", dois=doi)
        self.dois = doi
        return [doi]

    def _get_journal_doctype(self, article: ET.Element):
        self.logger.msg("Parsing journal doctype for article", dois=self.dois)
        journal_doctype_raw = article.find("front/..").get("article-type")
        if not journal_doctype_raw:
            return
        try:
            journal_doctype = self.article_type_mapping[journal_doctype_raw]
        except KeyError:
            journal_doctype = "other"
        if "other" in journal_doctype:
            self.logger.warning(
                "There are unmapped article types for article",
                journal_doctype=journal_doctype,
            )
        return journal_doctype

    def _get_arxiv_eprints(self, article: ET.Element):
        arxivs_raw = get_text_value(
            article.find("front/article-meta/article-id/[@pub-id-type='arxiv']")
        )
        if not arxivs_raw:
            return
        arxiv_eprint = arxivs_raw.lower().replace("arxiv:", "")
        if not arxiv_eprint:
            return
        return {"value": arxiv_eprint}

    def _get_authors(self, article: ET.Element):
        contributions = article.findall(
            "front/article-meta/contrib-group/contrib[@contrib-type='author']"
        )
        authors = []
        for contribution in contributions:
            surname = get_text_value(contribution.find("name/surname"))
            given_names = get_text_value(contribution.find("name/given-names"))
            email = get_text_value(contribution.find("email"))
            affiliations = contribution.findall("aff")
            full_affiliation = []
            for affiliation in affiliations:
                country = get_text_value(
                    affiliation.find(
                        "country",
                    )
                )
                institution = get_text_value(
                    affiliation.find(
                        "institution",
                    )
                )
                if country:
                    country = country.capitalize()
                full_affiliation.append(
                    {"institution": institution, "country": country}
                )

            if not all([surname, given_names, email]) and not full_affiliation:
                pass
            else:
                authors.append(
                    {
                        "surname": surname,
                        "given_names": given_names,
                        "email": email,
                        "affiliations": full_affiliation,
                    }
                )
        return authors
