from django.contrib import admin
from .models import EmailTemplate, EmailLog
from django_summernote.admin import SummernoteModelAdminMixin


class EmailTemplateAdmin(SummernoteModelAdminMixin, admin.ModelAdmin):
    list_display = ["template_key", "subject", "from_email", "to_email"]
    save_as = True
    summernote_fields = ("html_template",)


admin.site.register(EmailTemplate, EmailTemplateAdmin)


class EmailLogAdmin(admin.ModelAdmin):
    list_display = [
        "email_template",
        "subject",
        "from_email",
        "to_email",
        "sent_status",
        "sent_at",
    ]
    readonly_fields = [
        "email_template",
        "subject",
        "from_email",
        "to_email",
        "sent_status",
        "sent_at",
        "error_message",
    ]


admin.site.register(EmailLog, EmailLogAdmin)
