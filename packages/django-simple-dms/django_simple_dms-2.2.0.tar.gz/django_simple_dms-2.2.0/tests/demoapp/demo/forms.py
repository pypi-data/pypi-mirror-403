from django import forms


class UploadFileForm(forms.Form):
    tags = forms.CharField()
    file = forms.FileField()
