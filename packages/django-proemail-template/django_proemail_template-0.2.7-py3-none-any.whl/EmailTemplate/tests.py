from django.test import TestCase
from django.test import Client
from .models import EmailTemplate

# Create your tests here.
#python manage.py dumpdata EmailTemplate > data.json 

class EmailTest(TestCase):
    fixtures = ['data.json',]

    def setUp(self):
        self.client = Client()

    def test_multiple_addresses(self):
        print('aa')
        context={}
        context['user']='test_user'
        EmailTemplate.send('TEST', context,)