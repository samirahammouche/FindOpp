from django import forms

CATEGORY_CHOICES = [
    ("hackathon", "Hackathon"),
    ("scholarship", "Scholarship"),
    ("event", "Event"),
    ("club", "Club"),
]
STATUS_CHOICES = [
    ("", "Status: all"), ("draft", "Draft"), ("pending", "Pending"), ("approved", "Approved"),
    ("rejected", "Rejected"), ("expired", "Expired"),
]
LEVEL_CHOICES = [("bachelor", "Bachelor's degree"), ("master", "Master"), ("phd", "PhD")]
FUNDING_CHOICES = [("fully_funded", "Fully funded"), ("stipend", "Stipend"), ("prize", "Prize"), ("free", "Free")]
REGION_CHOICES = [
    ("", "Choose a region"), ("Algeria", "Algeria"), ("North Africa", "North Africa"), ("Africa", "Africa"),
    ("Europe", "Europe"), ("Middle East", "Middle East"), ("Worldwide", "Worldwide"),
]
CURRENCY_CHOICES = [("DZD", "DZD"), ("EUR", "EUR"), ("USD", "USD")]
ORG_TYPE_CHOICES = [("university", "University"), ("company", "Company"), ("ngo", "NGO"), ("club", "Student club")]

DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class PublicationFilterForm(forms.Form):
    """Filters of "My publications" (GET form)."""

    search = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Search publications…"}))
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES)
    category = forms.ChoiceField(required=False, choices=[("", "Category: all")] + CATEGORY_CHOICES)
    ordering = forms.ChoiceField(required=False, choices=[
        ("newest", "Date: newest"), ("oldest", "Date: oldest"),
        ("deadline", "Deadline: soonest"), ("views", "Most viewed"),
    ])


class PublicationForm(forms.Form):
    """"Create a publication" form. The data is sent to the Organizer service."""

    category = forms.ChoiceField(choices=CATEGORY_CHOICES, widget=forms.RadioSelect, initial="hackathon")
    # Opportunity details
    title = forms.CharField(label="Publication title", max_length=200)
    short_description = forms.CharField(label="Short description", max_length=300, required=False,
                                        widget=forms.Textarea(attrs={"rows": 2}))
    full_description = forms.CharField(label="Full description", required=False,
                                       widget=forms.Textarea(attrs={"rows": 7}))
    cover_image = forms.FileField(label="Cover image", required=False,
                                  widget=forms.ClearableFileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}))
    location = forms.CharField(label="Location", max_length=150, required=False,
                               widget=forms.TextInput(attrs={"placeholder": "Alger · Campus"}))
    is_remote = forms.BooleanField(label="Remote", required=False)
    application_link = forms.URLField(label="External application link", required=False,
                                      widget=forms.URLInput(attrs={"placeholder": "https://"}))
    # Eligibility
    study_levels = forms.MultipleChoiceField(choices=LEVEL_CHOICES, required=False,
                                             widget=forms.CheckboxSelectMultiple)
    fields_of_study = forms.CharField(label="Fields of study", required=False,
                                      help_text="Separate with commas",
                                      widget=forms.TextInput(attrs={"placeholder": "Computer science, Robotics"}))
    eligible_region = forms.ChoiceField(label="Eligible country or region", choices=REGION_CHOICES, required=False)
    open_to_all_nationalities = forms.BooleanField(label="Open to all nationalities", required=False)
    # Funding and dates
    funding_type = forms.ChoiceField(choices=FUNDING_CHOICES, widget=forms.RadioSelect, required=False)
    amount = forms.DecimalField(label="Amount", required=False, min_value=0, max_digits=12, decimal_places=2,
                                widget=forms.NumberInput(attrs={"placeholder": "150000"}))
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, initial="DZD")
    start_date = forms.DateField(label="Start date", required=False, widget=DATE)
    end_date = forms.DateField(label="End date", required=False, widget=DATE)
    application_deadline = forms.DateField(label="Application deadline", required=False, widget=DATE)

    def clean_fields_of_study(self):
        raw = self.cleaned_data["fields_of_study"]
        return [item.strip() for item in raw.split(",") if item.strip()]

    def clean(self):
        data = super().clean()
        start, end, deadline = data.get("start_date"), data.get("end_date"), data.get("application_deadline")
        if start and end and end < start:
            self.add_error("end_date", "The end date must be after the start date.")
        if deadline and start and deadline > start:
            self.add_error("application_deadline", "The deadline must be before the start date.")
        return data

    def to_api(self):
        """cleaned_data -> JSON for the API (the file is sent separately)."""
        data = {k: v for k, v in self.cleaned_data.items() if k != "cover_image"}
        for key in ("start_date", "end_date", "application_deadline"):
            data[key] = data[key].isoformat() if data[key] else None
        data["amount"] = str(data["amount"]) if data["amount"] is not None else None
        return data

    @classmethod
    def initial_from_api(cls, publication):
        """Publication from the API -> initial values of the form (edit page)."""
        initial = {name: publication.get(name) for name in cls.base_fields if name != "cover_image"}
        initial["fields_of_study"] = ", ".join(publication.get("fields_of_study") or [])
        return initial


class ProfileForm(forms.Form):
    """Organization profile (public identity on FindOpp)."""

    name = forms.CharField(label="Organization name", max_length=150)
    org_type = forms.ChoiceField(label="Type", choices=ORG_TYPE_CHOICES)
    city = forms.CharField(label="City", max_length=100)
    description = forms.CharField(label="Description", required=False, widget=forms.Textarea(attrs={"rows": 4}))
    website = forms.URLField(label="Website", required=False)
    linkedin = forms.URLField(label="LinkedIn", required=False)
    instagram = forms.URLField(label="Instagram", required=False)
    logo = forms.FileField(label="Logo", required=False,
                           widget=forms.ClearableFileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}))
    cover_image = forms.FileField(label="Cover image", required=False,
                                  widget=forms.ClearableFileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}))


class ContactForm(forms.Form):
    contact_email = forms.EmailField(label="Contact email")
    phone = forms.CharField(label="Phone", max_length=30, required=False)


class PasswordForm(forms.Form):
    old_password = forms.CharField(label="Current password", widget=forms.PasswordInput)
    new_password = forms.CharField(label="New password", min_length=8, widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirm the new password", widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        if data.get("new_password") != data.get("confirm_password"):
            self.add_error("confirm_password", "The two passwords are different.")
        return data


def add_api_errors(form, error):
    """Shows the validation errors returned by the API on the right fields."""
    for field, messages in error.data.items():
        text = " ".join(messages) if isinstance(messages, list) else str(messages)
        form.add_error(field if field in form.fields else None, text)
