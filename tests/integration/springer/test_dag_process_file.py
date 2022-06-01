import base64
import datetime
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pytest
from airflow import DAG
from airflow.models import DagBag
from airflow.utils.state import DagRunState
from busypie import SECOND, wait
from freezegun import freeze_time
from pytest import fail, fixture, raises
from springer.dag_process_file import (
    springer_enhance_file,
    springer_enrich_file,
    springer_parse_file,
    springer_validate_record,
)

DAG_NAME = "springer_process_file"


@fixture
def dag():
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    assert dagbag.import_errors.get(f"dags/{DAG_NAME}.py") is None
    return dagbag.get_dag(dag_id=DAG_NAME)


@fixture
def article():
    data_dir = "./data/"
    test_file = "ftp_PUB_19-01-29_20-02-10_JHEP.zip"

    def extract_zip_to_article(zip_filename):
        with ZipFile(zip_filename, "r") as zip_file:
            return [
                zip_file.read(filename)
                for filename in map(lambda x: x.filename, zip_file.filelist)
                if ".Meta" in filename or ".scoap" in filename
            ][0]

    article = ET.fromstring(extract_zip_to_article(data_dir + test_file))

    return article


def test_dag_loaded(dag: DAG):
    assert dag is not None
    assert len(dag.tasks) == 4


def test_dag_run(dag: DAG, article):
    id = datetime.datetime.utcnow().strftime(
        "test_springer_dag_process_file_%Y-%m-%dT%H:%M:%S.%f"
    )
    dagrun = dag.create_dagrun(
        DagRunState.QUEUED,
        run_id=id,
        conf={"file": base64.b64encode(ET.tostring(article)).decode()},
    )
    wait().at_most(60, SECOND).until(lambda: __test_dagrun_state(dagrun))


def test_dag_run_no_input_file(dag: DAG):
    id = datetime.datetime.utcnow().strftime(
        "test_springer_dag_process_file_%Y-%m-%dT%H:%M:%S.%f"
    )
    dagrun = dag.create_dagrun(DagRunState.QUEUED, run_id=id)
    wait().at_most(60, SECOND).until(lambda: __test_dagrun_fails(dagrun))


def test_dag_parse_file(article):
    springer_parse_file(
        params={"file": base64.b64encode(ET.tostring(article)).decode()}
    )


publisher = "Springer"

generic_pseudo_parser_output = {
    "abstract": "this is abstracts",
    "copyright_holder": "copyright_holder",
    "copyright_year": "2020",
    "copyright_statement": "copyright_statement",
    "copyright_material": "copyright_material",
    "date_published": "2022-05-20",
    "title": "title",
    "subtitle": "subtitle",
}


expected_output = {
    "abstracts": [{"value": "this is abstracts", "source": publisher}],
    "acquisition_source": {
        "source": publisher,
        "method": publisher,
        "date": "2022-05-20T00:00:00",
    },
    "copyright": [
        {
            "holder": "copyright_holder",
            "year": "2020",
            "statement": "copyright_statement",
            "material": "copyright_material",
        }
    ],
    "imprints": [{"date": "2022-05-20", "publisher": publisher}],
    "record_creation_date": "2022-05-20T00:00:00",
    "titles": [{"title": "title", "subtitle": "subtitle", "source": publisher}],
}

empty_generic_pseudo_parser_output = {
    "abstract": "",
    "copyright_holder": "",
    "copyright_year": "",
    "copyright_statement": "",
    "copyright_material": "",
    "date_published": "",
    "title": "",
    "subtitle": "",
}


expected_output_from_empty_input = {
    "abstracts": [{"value": "", "source": publisher}],
    "acquisition_source": {
        "source": publisher,
        "method": publisher,
        "date": "2022-05-20T00:00:00",
    },
    "copyright": [{"holder": "", "year": "", "statement": "", "material": ""}],
    "imprints": [{"date": "", "publisher": publisher}],
    "record_creation_date": "2022-05-20T00:00:00",
    "titles": [{"title": "", "subtitle": "", "source": publisher}],
}


@pytest.mark.parametrize(
    "test_input, expected, publisher",
    [
        pytest.param(generic_pseudo_parser_output, expected_output, publisher),
        pytest.param(
            empty_generic_pseudo_parser_output,
            expected_output_from_empty_input,
            publisher,
        ),
    ],
)
@freeze_time("2022-05-20")
def test_dag_enhance_file(test_input, expected, publisher):
    assert expected == springer_enhance_file(test_input)


def test_dag_enrich_file(assertListEqual):
    input_article = {
        "arxiv_eprints": [{"value": "2112.01211"}],
        "curated": "Test Value",
        "citeable": "Test Value",
        "files": "Test Value",
    }
    assertListEqual(
        {
            "arxiv_eprints": [
                {"value": "2112.01211", "categories": list(set(["hep-th", "hep-ph"]))}
            ],
            "$schema": "http://repo.qa.scoap3.org/schemas/hep.json",
        },
        springer_enrich_file(input_article),
    )


def test_dag_validate_file_pass(article):
    article = {
        "dois": [{"value": "10.1007/JHEP01(2019)210"}],
        "arxiv_eprints": [{"value": "1811.06048", "categories": ["hep-th"]}],
        "page_nr": [29],
        "authors": [
            {
                "surname": "Kubo",
                "given_names": "Naotaka",
                "email": "naotaka.kubo@yukawa.kyoto-u.ac.jp",
                "affiliations": [
                    {
                        "value": "Center for Gravitational Physics, Yukawa Institute for Theoretical Physics, Kyoto University, Sakyo-ku, Kyoto, 606-8502, Japan",
                        "organization": "Kyoto University",
                        "country": "Japan",
                    }
                ],
                "full_name": "Kubo, Naotaka",
            },
            {
                "surname": "Moriyama",
                "given_names": "Sanefumi",
                "email": "moriyama@sci.osaka-cu.ac.jp",
                "affiliations": [
                    {
                        "value": "Department of Physics, Graduate School of Science, Osaka City University, Sumiyoshi-ku, Osaka, 558-8585, Japan",
                        "organization": "Osaka City University",
                        "country": "Japan",
                    },
                    {
                        "value": "Nambu Yoichiro Institute of Theoretical and Experimental Physics (NITEP), Sumiyoshi-ku, Osaka, 558-8585, Japan",
                        "organization": "Nambu Yoichiro Institute of Theoretical and Experimental Physics (NITEP)",
                        "country": "Japan",
                    },
                    {
                        "value": "Osaka City University Advanced Mathematical Institute (OCAMI), Sumiyoshi-ku, Osaka, 558-8585, Japan",
                        "organization": "Osaka City University Advanced Mathematical Institute (OCAMI)",
                        "country": "Japan",
                    },
                ],
                "full_name": "Moriyama, Sanefumi",
            },
            {
                "surname": "Nosaka",
                "given_names": "Tomoki",
                "email": "nosaka@yukawa.kyoto-u.ac.jp",
                "affiliations": [
                    {
                        "value": "School of Physics, Korea Institute for Advanced Study, Dongdaemun-gu, Seoul, 02455, Korea",
                        "organization": "School of Physics, Korea Institute for Advanced Study",
                        "country": "Korea",
                    }
                ],
                "full_name": "Nosaka, Tomoki",
            },
        ],
        "license": [
            {
                "license": "CC-BY-3.0",
                "url": "https://creativecommons.org/licenses/by/3.0",
            }
        ],
        "collections": [{"primary": "Journal of High Energy Physics"}],
        "publication_info": [
            {
                "journal_title": "Journal of High Energy Physics",
                "journal_volume": "2019",
                "year": 2019,
                "journal_issue": "1",
                "artid": "JHEP012019210",
                "page_start": "1",
                "page_end": "29",
                "material": "article",
            }
        ],
        "abstracts": [
            {
                "value": "It was known that quantum curves and super Chern-Simons matrix models correspond to each other. From the viewpoint of symmetry, the algebraic curve of genus one, called the del Pezzo curve, enjoys symmetry of the exceptional algebra, while the super Chern-Simons matrix model is described by the free energy of topological strings on the del Pezzo background with the symmetry broken. We study the symmetry breaking of the quantum cousin of the algebraic curve and reproduce the results in the super Chern-Simons matrix model.",
                "source": "Springer",
            }
        ],
        "acquisition_source": {
            "source": "Springer",
            "method": "Springer",
            "date": "2022-06-02T10:59:48.860085",
        },
        "copyright": [{"holder": "SISSA, Trieste, Italy", "year": 2019}],
        "imprints": [{"date": "2019-01-28", "publisher": "Springer"}],
        "record_creation_date": "2022-06-02T10:59:48.860085",
        "titles": [
            {
                "title": "Symmetry breaking in quantum curves and super Chern-Simons matrix models",
                "source": "Springer",
            }
        ],
        "$schema": "http://repo.qa.scoap3.org/schemas/hep.json",
    }
    try:
        springer_validate_record(article)
    except Exception:
        fail()


def test_dag_validate_file_fails(article):
    article = {}
    raises(Exception, springer_validate_record, article)


def test_dag_process_file_no_input_file(article):
    raises(Exception, springer_parse_file)


def __test_dagrun_fails(dagrun):
    dagrun.update_state()
    return not dagrun.get_state() == DagRunState.FAILED


def __test_dagrun_state(dagrun):
    dagrun.update_state()
    assert dagrun.get_state() != DagRunState.FAILED
    return (
        not dagrun.get_state() == DagRunState.QUEUED
        and not dagrun.get_state() == DagRunState.RUNNING
    )
