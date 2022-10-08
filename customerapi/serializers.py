from rest_framework import serializers
from .models import Customer, CustomerHistory


class CustomerHistorySerializer(serializers.ModelSerializer):
    # Add this so that it will be included inside the validated_data
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CustomerHistory
        fields = ['id', 'history']


class CustomerSerializers(serializers.ModelSerializer):
    # this should represent the array from the UI and we need to add it as part of the field for the parent.
    # we add, required=False to not ask it to be filled up from the request call.
    customer_histories = CustomerHistorySerializer(many=True, required=False)
    # so it be attached to the validate_data serializer
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Customer
        fields = ['id', 'name', 'age', 'customer_histories']

    def create(self, validated_data):
        incoming_history_data = validated_data.pop('customer_histories')
        customer = Customer.objects.create(**validated_data)
        for history in incoming_history_data:
            CustomerHistory.objects.create(
                customer=customer,
                history=history.get('history')
            )
        return customer

    def update(self, instance, validated_data):
        # get parent primary key
        customer_pk = validated_data.get('id')
        # get the incoming customer histories
        incoming_history_data = validated_data.pop('customer_histories')
        # save the parent first
        instance.name = validated_data.get('name')
        instance.age = validated_data.get('age')
        instance.save()

        # get original child record
        original_customer_histories = CustomerHistory.objects.filter(customer_id = customer_pk)

        # get all incoming history ids
        incoming_history_data_ids = []
        for i in incoming_history_data:
            incoming_history_data_ids.append(i.get('id'))

        # get original customer histories by incoming history ids. Here, we select only those ids that need to be updated.
        customer_histories_by_ids = original_customer_histories.filter(pk__in=incoming_history_data_ids)

        # create customer_history_ids to track those ids that have update
        customer_history_ids = []
        for i in incoming_history_data:
            customer_history = customer_histories_by_ids.filter(
                pk=i.get('id'))
            if customer_history.exists():
                customer_history.update(history=i.get('history'))
            else:
                customer_history.create(
                    customer=instance,
                    history=i.get('history'))
            customer_history_ids.append(i.get('id'))

        # compare the incoming child to the existing child. If the incoming is less than the saved child, we delete those rows that have no updates.
        if len(incoming_history_data) < original_customer_histories.count():
            # exclude those childs from the original record that have no update
            customer_histories_no_update = original_customer_histories.exclude(
                pk__in=customer_history_ids)
            if customer_histories_no_update.exists():
                for i in customer_histories_no_update:
                    i.delete()

        return instance
