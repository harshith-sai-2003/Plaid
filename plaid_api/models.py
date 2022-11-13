from django.db import models

# Create your models here.
class PlaidCredential(models.Model):
    user=models.ForeignKey('auth.User',
    related_name='plaid_credentials',on_delete=models.CASCADE)
    access_token=models.CharField(max_length=255)
