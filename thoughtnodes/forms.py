from django import forms
from . import models

class CreateThoughtnode(forms.ModelForm):
    class Meta:
        model = models.Thoughtnode
        fields = [
            'title',
            'query',
            'prompt',
            'frequency',
        ]