from django.db.models import QuerySet

from case_studies.models import CaseStudy


def get_case_studies_list() -> QuerySet[CaseStudy]:
    """
    Get all case study objects.
    """
    return CaseStudy.objects.all()
