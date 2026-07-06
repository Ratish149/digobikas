from django.db.models import QuerySet

from empowerment_program.models import (
    CohortVolunteer,
    EmpowermentProgram,
    EmpowermentProgramCohort,
)


def get_programs_list() -> QuerySet[EmpowermentProgram]:
    """
    Get all empowerment programs optimized with prefetch_related for cohorts and volunteers.
    """
    return EmpowermentProgram.objects.prefetch_related("cohorts", "cohorts__volunteers")


def get_cohorts_list() -> QuerySet[EmpowermentProgramCohort]:
    """
    Get all cohorts optimized with select_related for the program and prefetch_related for volunteers.
    """
    return EmpowermentProgramCohort.objects.select_related("program").prefetch_related("volunteers")


def get_volunteers_list() -> QuerySet[CohortVolunteer]:
    """
    Get all volunteers optimized with select_related for cohort and program.
    """
    return CohortVolunteer.objects.select_related("cohort", "cohort__program")
