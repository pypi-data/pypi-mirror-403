from datetime import date
from functools import reduce

from dateutil.relativedelta import relativedelta
from django.db import models, transaction

from huscy.attributes.models import AttributeSet
from huscy.participations.models import Participation
from huscy.subject_contact_history.models import ContactHistoryItem
from huscy.subject_contact_history.services import create_contact_history_item
from huscy.pseudonyms.services import (
    get_subjects as get_subjects_by_pseudonym,
    get_or_create_pseudonym,
)
from huscy.recruitment.models import ParticipationRequest, RecruitmentCriteria, SubjectGroup


#################################################
# subject groups
#################################################

@transaction.atomic
def create_subject_group(experiment, name, description=''):
    subject_group = SubjectGroup.objects.create(
        experiment=experiment,
        name=name,
        description=description,
        order=SubjectGroup.objects.filter(experiment=experiment).count(),
    )
    RecruitmentCriteria.objects.create(subject_group=subject_group)
    return subject_group


def delete_subject_group(subject_group):
    subject_groups_queryset = SubjectGroup.objects.filter(experiment=subject_group.experiment)

    if subject_groups_queryset.count() == 1:
        raise ValueError('Cannot delete subject group. At least one subject group must remain for '
                         'the experiment.')

    (subject_groups_queryset.filter(order__gt=subject_group.order)
                            .update(order=models.F('order') - 1))

    subject_group.delete()


def get_subject_groups(experiment):
    subject_groups_queryset = experiment.subject_groups.all()

    if not subject_groups_queryset.exists():
        create_subject_group(experiment, name='Subject group 1')

    return subject_groups_queryset


def update_subject_group(subject_group, name='', description='', order=None):
    subject_group.name = name or subject_group.name
    subject_group.description = description or subject_group.description

    if (order is not None and subject_group.order != order):
        if subject_group.order < order:
            SubjectGroup.objects.filter(order__gt=subject_group.order,
                                        order__lte=order).update(order=models.F('order') - 1)
        if subject_group.order > order:
            SubjectGroup.objects.filter(order__lt=subject_group.order,
                                        order__gte=order).update(order=models.F('order') + 1)
        subject_group.order = order

    subject_group.save()
    return subject_group


#################################################
# recruitment criteria
#################################################

def update_recruitment_criteria(subject_group,
                                minimum_age_in_months=None,
                                maximum_age_in_months=None,
                                attribute_filterset=None):
    recruitment_criteria = subject_group.recruitment_criteria.latest('id')

    if recruitment_criteria.participation_requests.exists():
        recruitment_criteria = RecruitmentCriteria.objects.create(subject_group=subject_group)

    if minimum_age_in_months is not None:
        recruitment_criteria.minimum_age_in_months = minimum_age_in_months
    if maximum_age_in_months is not None:
        recruitment_criteria.maximum_age_in_months = maximum_age_in_months
    if attribute_filterset is not None:
        recruitment_criteria.attribute_filterset = attribute_filterset

    recruitment_criteria.save()

    return recruitment_criteria


def apply_recruitment_criteria(recruitment_criteria):
    filtered_attribute_sets = filter_attributesets_by_attribute_filterset(recruitment_criteria)
    pseudonyms = [attribute_set.pseudonym for attribute_set in filtered_attribute_sets]
    pre_filtered_subjects = get_subjects_by_pseudonym(pseudonyms)
    matching_subjects = filter_subjects_by_age(pre_filtered_subjects, recruitment_criteria)
    return (matching_subjects.select_related('contact')
                             .prefetch_related('legal_representatives'))


def filter_attributesets_by_attribute_filterset(recruitment_criteria):
    queryset = models.Q()
    for path, condition in recruitment_criteria.attribute_filterset.items():
        queryset &= reduce(
            lambda result, value: extend_queryset(result, path, condition, value),
            condition['values'],
            models.Q()
        )
    return AttributeSet.objects.filter(queryset)


def extend_queryset(queryset, path, condition, value):
    query = models.Q(**{f'attributes__{path}__{condition["operator"].lstrip("-")}': value})
    if condition['operator'].startswith('-'):
        query = ~query
    return queryset | query


def filter_subjects_by_age(subjects, recruitment_criteria):
    today = date.today()
    latest_date_of_birth = (
        today - relativedelta(months=recruitment_criteria.minimum_age_in_months)
    )
    earliest_date_of_birth = (
        today - relativedelta(months=recruitment_criteria.maximum_age_in_months)
    )
    return subjects.filter(contact__date_of_birth__lte=latest_date_of_birth,
                           contact__date_of_birth__gte=earliest_date_of_birth)


#################################################
# participation requests
#################################################

@transaction.atomic
def create_or_update_participation_request(subject, recruitment_criteria, action, user):
    subject_group = recruitment_criteria.subject_group
    experiment = subject_group.experiment
    project = experiment.project
    participation = None

    pseudonym = get_or_create_pseudonym(
        subject=subject,
        content_type='recruitment.participationrequest',
        object_id=experiment.id
    )

    match action:
        case 'declined':
            status = ParticipationRequest.STATUS.invited
            create_contact_history_item(subject, project, creator=user,
                                        status=ContactHistoryItem.Status.INVITED_BY_PHONE)
        case 'invited_by_email':
            status = ParticipationRequest.STATUS.invited
            create_contact_history_item(subject, project, creator=user,
                                        status=ContactHistoryItem.Status.INVITED_BY_EMAIL)
        case 'invited_by_phone':
            status = ParticipationRequest.STATUS.invited
            participation_pseudonym = get_or_create_pseudonym(
                subject=subject,
                content_type='participations.participation',
                object_id=experiment.id
            )
            participation = Participation.objects.create(
                pseudonym=participation_pseudonym,
                experiment=experiment,
                status=Participation.STATUS.pending,
            )
            create_contact_history_item(subject, project, creator=user,
                                        status=ContactHistoryItem.Status.INVITED_BY_PHONE)
        case 'unreachable_by_phone':
            status = ParticipationRequest.STATUS.pending
            create_contact_history_item(subject, project, creator=user,
                                        status=ContactHistoryItem.Status.DID_NOT_ANSWER_THE_PHONE)
        case _:
            raise Exception

    participation_request, created = ParticipationRequest.objects.get_or_create(
        pseudonym=pseudonym.code,
        recruitment_criteria=recruitment_criteria,
        defaults=dict(
            participation=participation,
            status=status,
        ),
    )

    if not created and not participation_request.status == status:
        participation_request.status = status
        participation_request.save(update_fields=['status'])

    if participation and not participation_request.participation:
        participation_request.participation = participation
        participation_request.save(update_fields=['participation'])

    return participation_request


"""
def get_participation_requests_for_experiment(experiment):
    return (ParticipationRequest.objects
                                .filter(attribute_filterset__subject_group__experiment=experiment))


def get_participation_requests(subject=None, attribute_filterset=None):
    if attribute_filterset is None and subject is None:
        raise ValueError('Expected either attribute_filterset or subject args')

    pseudonyms = []
    if subject:
        content_type = ContentType.objects.get_by_natural_key('recruitment', 'participationrequest')
        pseudonyms = (Pseudonym.objects.filter(subject=subject, content_type=content_type)
                                       .values_list('code', flat=True))
    if attribute_filterset and subject:
        return ParticipationRequest.objects.filter(pseudonym__in=pseudonyms,
                                                   attribute_filterset=attribute_filterset)
    elif attribute_filterset:
        return ParticipationRequest.objects.filter(attribute_filterset=attribute_filterset)
    return ParticipationRequest.objects.filter(pseudonym__in=pseudonyms)
"""
