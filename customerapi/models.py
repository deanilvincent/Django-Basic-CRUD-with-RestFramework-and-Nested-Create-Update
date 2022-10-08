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
