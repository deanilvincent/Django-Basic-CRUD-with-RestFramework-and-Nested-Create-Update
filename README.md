# Django CRUD with Nested Create & Update Repository
A basic CRUD (Create, Read, Update & Delete) operations project repository that I compiled while I'm building my skills in Django Framework. I'm open to suggestions and improvements!

## DIY (Do it yourself)
### Setup the project
- Create environment `py -m venv .venv`
- Install Django `pipenv install django`
- Activate environment via visual studio code by: Ctrl+Shift+P, Select Interpreter then choose your virtual env.
- Start new project: `django-admin startproject name_of_app .`
- Create app or endpoint app: `python manage.py startapp customerapi`
- Install `pip install djangorestframework`
- Install database package. For this repo, I'm using Postgresql. Run this `pip install psycopg2`
- Go to project app [settings.py](/app/settings.py) and under `[INSTALLED_APPS]`, add the project and the rest framework. Something like this:
```
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'customerapi'
]
```
For setting up the database connection, under settings.py, go to the `DATABASES`. Example below:
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'Database_Name', # Make sure you already created your database first on the server.
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost'
    }
}
```
### Create Model ([models.py](/customerapi/models.py))
```
from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100, default='na')
    age = models.IntegerField(max_length=3)

    def __str__(self):
        return self.name

class CustomerHistory(models.Model):
    history = models.CharField(max_length=100)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='customer_histories')

    def __str__(self):
        return self.history
```
### Run Migrations
- Run first the initial migration. `python manage.py migrate`.
- Now, run this command to create a migration file or the snapshot file for your new models that are under the customerapi migrations folder. `python manage.py makemigrations customerapi` then `python manage.py migrate` to make the database changes.

### Create Serializers ([customerapi/serializers.py](customerapi/serializers.py))
- Since we're dealing with nested models, we need to create custom create and update methods for our customer and customer history serializer to allow writable nested serializers. [source](https://www.django-rest-framework.org/api-guide/relations/#writable-nested-serializers)
```
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

```
- When calling the `create` or `update` method, your array should be something like this:

#### For Create:
```
{
    "name": "John Doe", 
    "age": 24,
    "customer_histories": [
        {
            "history": "Order new stuff"
        },
        {
            "history": "Get voucher"
        }
    ]
}
```
This will create a data to the customers table with proper relationships with the customer history table.
#### For Update:
- The use case for this `update` method is when we need to update a changes for both parent and child from a single request.
```
{
    "id": 1, // Parent PK
    "name": "John Doe Jr.", 
    "age": 23,
    "customer_histories": [
        {
            "id": 1, // Child pk
            "history": "Order new stuff update"
        },
        {
            "id": 2, // Child pk
            "history": "Get voucher update"
        }
    ]
}
```
We need to specify the `id` and the `customer_histories ids` to properly update the parent and child data. In the current code `update` method. If the `customer_histories` is missing the other child's data from an array, then it will be deleted since there's no update found for that specific child. If there's a new array of data with an id of `0`, then it will be treated as a new child that needs to be created. (Let me know if there's something I need to improve. I'm open to suggestions!)

### Create views ([customerapi/views.py](customerapi/views.py))
- This will handle our Restful Services endpoints.
```
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
```
### Register Endpoints ([app/urls.py](app/urls.py))
```
from django.contrib import admin
from django.urls import path, include
from customerapi import views
from todoapi.router import router

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/customers/', views.customers),
    path('api/customers/<int:id>', views.customerDetail)
]
```
## For Non-Nested Sample:
For non-nested sample project, you can check the [todoapi/](todoapi) project where it has its own simple model, serializers, viewsets and router.

- [todoapi/models](todoapi/models.py)
```
from django.db import models

class Todo(models.Model):
    item = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```
- [todoapi/serializers](todoapi/serializers.py)
```
from pyexpat import model
from rest_framework import serializers
from .models import Todo

class TodoSerializers(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = '__all__' # all columns
```
- [todoapi/viewsets](todoapi/viewsets.py)
```
from rest_framework import viewsets
from .serializers import TodoSerializers
from .models import Todo


class TodoViewsets(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializers
```
- [todoapi/router](todoapi/router.py)
```
from rest_framework import routers
from .viewsets import TodoViewsets
router = routers.DefaultRouter()
router.register('todo', TodoViewsets)
```
- Register the router in the [app/urls.py](app/urls.py)
```
from django.urls import path, include
from todoapi.router import router
...
urlpatterns = [
    path('api/', include(router.urls))
    ...
]
```
