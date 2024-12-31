from django import forms
from django.contrib.auth import get_user_model

from .models import ChatType, Room

User = get_user_model()


class PrivateChatForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.all(), label="Chat with")

    class Meta:
        model = Room
        fields = ["recipient"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["recipient"].queryset = User.objects.exclude(id=self.user.id)

    def save(self, commit=True):
        room = super().save(commit=False)
        room.chat_type = ChatType.PRIVATE
        room.creator = self.user
        if commit:
            room.save()
            room.participants.add(self.user, self.cleaned_data["recipient"])
        return room


class GroupChatForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Participants",
    )

    class Meta:
        model = Room
        fields = ["name", "participants"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["participants"].queryset = User.objects.exclude(id=self.user.id)

    def save(self, commit=True):
        room = super().save(commit=False)
        room.chat_type = ChatType.GROUP
        room.creator = self.user
        if commit:
            room.save()
            participants = self.cleaned_data["participants"]
            room.participants.add(self.user, *participants)
        return room
