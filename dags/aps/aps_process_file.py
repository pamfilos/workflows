import json

import pendulum
from airflow.decorators import dag, task
from aps.parser import APSParser
from common.enhancer import Enhancer
from common.enricher import Enricher
from common.exceptions import EmptyOutputFromPreviousTask
from common.utils import create_or_update_article


def parse_aps(data):
    parser = APSParser()
    parsed = parser.parse(data)
    return parsed


def enhance_aps(parsed_file):
    return Enhancer()("APS", parsed_file)


def enrich_aps(enhanced_file):
    return Enricher()(enhanced_file)


@dag(schedule=None, start_date=pendulum.today("UTC").add(days=-1))
def aps_process_file():
    @task()
    def parse(**kwargs):
        if "params" in kwargs and "article" in kwargs["params"]:
            article = json.loads(kwargs["params"]["article"])
            return parse_aps(article)

    @task()
    def enhance(parsed_file):
        if not parsed_file:
            raise EmptyOutputFromPreviousTask("parse")
        return enhance_aps(parsed_file)

    @task()
    def enrich(enhanced_file):
        if not enhanced_file:
            raise EmptyOutputFromPreviousTask("enhance")
        return enrich_aps(enhanced_file)

    @task()
    def create_or_update(enriched_file):
        create_or_update_article(enriched_file)

    parsed_file = parse()
    enhanced_file = enhance(parsed_file)
    enriched_file = enrich(enhanced_file)
    create_or_update(enriched_file)


dag_for_aps_files_processing = aps_process_file()
