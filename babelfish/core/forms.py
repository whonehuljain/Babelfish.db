from django import forms
import re

class SqlConnectForm(forms.Form):
    username = forms.CharField(max_length=100, label='MySQL Username')
    password = forms.CharField(
        max_length=100, 
        widget=forms.PasswordInput, 
        label='MySQL Password'
    )
    hostname = forms.CharField(
        max_length=200, 
        initial='localhost', 
        label='Hostname/Host Address'
    )
    schema_name = forms.CharField(
        max_length=100, 
        label='Database Schema Name'
    )

class MongoConnectForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MongoDB Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'MongoDB Password'
        })
    )
    hostname = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hostname (e.g., localhost:27017 or cluster0.xxx.mongodb.net)'
        })
    )
    db_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Database Name'
        })
    )
    collection_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Collection Name'
        })
    )

    def clean_hostname(self):
        hostname = self.cleaned_data['hostname']
        hostname = hostname.rstrip('/')
        hostname = re.sub(r'^mongodb(\+srv)?://', '', hostname)
        return hostname