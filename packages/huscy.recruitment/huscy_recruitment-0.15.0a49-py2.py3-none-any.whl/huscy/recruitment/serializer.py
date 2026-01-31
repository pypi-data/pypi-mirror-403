from rest_framework import serializers

from huscy.recruitment import models, services


class ParticipationRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = models.ParticipationRequest
        fields = (
            'id',
            'created_at',
            'participation',
            'recruitment_criteria',
            'status',
            'status_display',
        )
        read_only_fields = 'created_at', 'participation', 'recruitment_criteria', 'status'

    """
    def to_representation(self, participation_request):
        response = super().to_representation(participation_request)
        if participation_request.status == models.ParticipationRequest.STATUS.get_value('pending'):
            try:
                recall = participation_request.recall.get()
            except Recall.DoesNotExist:
                return response

            # TODO: skip this, if appointment is in the past
            response['recall_appointment'] = AppointmentSerializer(recall.appointment).data
        return response
    """


class RecruitmentCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RecruitmentCriteria
        fields = (
            'id',
            'attribute_filterset',
            'maximum_age_in_months',
            'minimum_age_in_months',
        )

    def update(self, recruitment_criteria, validated_data):
        subject_group = self.context.get('subject_group')
        return services.update_recruitment_criteria(subject_group, **validated_data)


class SubjectGroupSerializer(serializers.ModelSerializer):
    recruitment_criteria = RecruitmentCriteriaSerializer(many=True, read_only=True)

    class Meta:
        model = models.SubjectGroup
        fields = (
            'id',
            'description',
            'experiment',
            'name',
            'order',
            'recruitment_criteria',
        )
        read_only_fields = ('experiment', )

    def create(self, validated_data):
        experiment = self.context['experiment']
        return services.create_subject_group(experiment, **validated_data)
