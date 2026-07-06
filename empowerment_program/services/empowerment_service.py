from django.db import transaction

from empowerment_program.models import (
    CohortVolunteer,
    EmpowermentProgram,
    EmpowermentProgramCohort,
)


def create_empowerment_program(
    *, title: str, content: str = None
) -> EmpowermentProgram:
    with transaction.atomic():
        program = EmpowermentProgram(title=title, content=content)
        program.full_clean()
        program.save()
        return program


def update_empowerment_program(
    *, program: EmpowermentProgram, **data
) -> EmpowermentProgram:
    with transaction.atomic():
        for field, value in data.items():
            setattr(program, field, value)
        program.full_clean()
        program.save()
        return program


def create_cohort(
    *,
    program: EmpowermentProgram,
    name: str,
    image=None,
    image_alt_description: str = None,
    volunteers_data: list = None,
) -> EmpowermentProgramCohort:
    with transaction.atomic():
        cohort = EmpowermentProgramCohort(
            program=program,
            name=name,
            image=image,
            image_alt_description=image_alt_description,
        )
        cohort.full_clean()
        cohort.save()

        if volunteers_data:
            for vol_data in volunteers_data:
                volunteer = CohortVolunteer(
                    cohort=cohort,
                    name=vol_data.get("name"),
                    image=vol_data.get("image"),
                    image_alt_description=vol_data.get("image_alt_description"),
                )
                volunteer.full_clean()
                volunteer.save()

        return cohort


def update_cohort(
    *, cohort: EmpowermentProgramCohort, **data
) -> EmpowermentProgramCohort:
    volunteers_data = data.pop("volunteers", None)
    with transaction.atomic():
        for field, value in data.items():
            setattr(cohort, field, value)
        cohort.full_clean()
        cohort.save()

        if volunteers_data is not None:
            keep_volunteers = []
            for vol_item in volunteers_data:
                vol_id = vol_item.get("id")
                if vol_id:
                    try:
                        volunteer = CohortVolunteer.objects.get(
                            id=vol_id, cohort=cohort
                        )
                        for k, v in vol_item.items():
                            if k != "id":
                                setattr(volunteer, k, v)
                        volunteer.full_clean()
                        volunteer.save()
                        keep_volunteers.append(volunteer.id)
                    except CohortVolunteer.DoesNotExist:
                        pass
                else:
                    volunteer = CohortVolunteer(
                        cohort=cohort,
                        name=vol_item.get("name"),
                        image=vol_item.get("image"),
                        image_alt_description=vol_item.get("image_alt_description"),
                    )
                    volunteer.full_clean()
                    volunteer.save()
                    keep_volunteers.append(volunteer.id)

            cohort.volunteers.exclude(id__in=keep_volunteers).delete()

        return cohort


def create_cohort_volunteer(
    *,
    cohort: EmpowermentProgramCohort,
    name: str,
    image=None,
    image_alt_description: str = None,
) -> CohortVolunteer:
    with transaction.atomic():
        volunteer = CohortVolunteer(
            cohort=cohort,
            name=name,
            image=image,
            image_alt_description=image_alt_description,
        )
        volunteer.full_clean()
        volunteer.save()
        return volunteer


def update_cohort_volunteer(
    *, cohort_volunteer: CohortVolunteer, **data
) -> CohortVolunteer:
    with transaction.atomic():
        for field, value in data.items():
            setattr(cohort_volunteer, field, value)
        cohort_volunteer.full_clean()
        cohort_volunteer.save()
        return cohort_volunteer
