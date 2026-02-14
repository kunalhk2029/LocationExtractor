from django import forms
from .models import ReelJob


class ReelUploadForm(forms.ModelForm):
    class Meta:
        model = ReelJob
        fields = ["source_url", "video_file"]

    def clean_video_file(self):
        video = self.cleaned_data.get("video_file")
        if not video:
            raise forms.ValidationError("Please upload a video file.")
        return video
