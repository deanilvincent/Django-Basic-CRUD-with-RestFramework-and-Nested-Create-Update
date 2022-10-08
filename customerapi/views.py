from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import CustomerSerializers
from .models import Customer


@api_view(['GET', 'POST'])
def customers(request):
    if request.method == 'GET':
        customers = Customer.objects.all()
        serializer = CustomerSerializers(customers, many=True)
        return Response(serializer.data)
    if request.method == 'POST':
        serializer = CustomerSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Data has been successfully created'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def customerDetail(request, id):
    try:
        customer = Customer.objects.get(pk=id)
    except Customer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CustomerSerializers(customer)
        return Response({'customer': serializer.data})

    if request.method == 'PUT':
        serializer = CustomerSerializers(customer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Data has been successfully saved.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        customer.delete()
        return Response({'message': 'Data has been successfully removed.'}, status=status.HTTP_200_OK)
