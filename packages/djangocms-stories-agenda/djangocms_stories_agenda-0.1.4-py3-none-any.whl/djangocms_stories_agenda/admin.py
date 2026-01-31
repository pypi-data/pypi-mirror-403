from django.contrib import admin
from django.utils.dateformat import DateFormat
from django.utils.translation import gettext as _, gettext_lazy
import djangocms_stories.admin as blog_admin
from djangocms_stories.admin import PostAdmin
from djangocms_stories.models import Post

from .conf import settings
from .misc import get_inline_instances as patched_get_inline_instances
from .models import PostExtension


# replace PostAdmin get_inlines function in order to hide event_start_date on
# regular blog posts
PostAdmin.get_inline_instances = patched_get_inline_instances


class PostExtensionInline(admin.StackedInline):
    model = PostExtension
    fields = [
        "event_start_date",
        "event_end_date",
        "is_pinned",
    ]
    classes = []
    extra = 1
    can_delete = False
    verbose_name = gettext_lazy("Event infos")
    verbose_name_plural = gettext_lazy("Event infos")
    min_num = 1
    max_num = 1

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if settings.RECURRENCE_IS_ENABLED and "recurrences" not in fields:
            fields.append("recurrences")
        return fields


blog_admin.register_extension(PostExtensionInline)


admin.site.unregister(Post)


@admin.register(Post)
class AgendaPostAdmin(PostAdmin):
    """Better layout of Post admin form"""

    list_display = [
        "application_name",
        "title",
        "get_event_dates",
        "date_published",
        "author",
        "state_indicator",
        "admin_list_actions",
    ]

    date_hierarchy = "extension__event_start_date"
    ordering = (
        "-extension__is_pinned",
        "-date_published",
    )

    _fieldsets = [
        (
            None,
            {
                "fields": [
                    "content__language",
                    "content__title",
                    "content__subtitle",
                    "content__slug",
                    [
                        "categories",
                        "app_config",
                    ],
                ]
            },
        ),
        (
            gettext_lazy("Info"),
            {
                "fields": [
                    ["tags"],
                    ["date_published", "date_published_end", "date_featured"],
                    ["enable_comments"],
                ],
                "classes": ("collapse",),
            },
        ),
        (
            gettext_lazy("Images"),
            {
                "fields": [["main_image", "main_image_thumbnail", "main_image_full"]],
                "classes": ("collapse",),
            },
        ),
        (
            _("SEO"),
            {
                "fields": [
                    "content__meta_title",
                    "content__meta_keywords",
                    "content__meta_description",
                ],
                "classes": ("collapse",),
            },
        ),
        (None, {"fields": (("date_created", "date_modified"),)}),
    ]
    _fieldset_extra_fields_position = {
        "content__abstract": (0, 1),
        "content__post_text": (0, 1),
        "sites": (1, 1, 0),
        "author": (1, 1, 0),
        "related": (1, 1, 0),
    }

    @admin.display(
        description=gettext_lazy("Application"),
        ordering="app_config__namespace",
    )
    def application_name(self, obj):
        return obj.app_config.namespace

    @admin.display(
        description=gettext_lazy("Event dates"),
        ordering="extension__event_start_date",
    )
    def get_event_dates(self, obj):
        extension = obj.extension.first()
        if extension is not None:
            start = extension.event_start_date
            end = extension.event_end_date
            df_start = DateFormat(start)
            df_end = DateFormat(end)
            DAY_FORMAT = _("jS")
            DAY_MONTH_FORMAT = _("jS F")
            DAY_MONTH_YEAR_FORMAT = _("jS F Y")

            if end is None:
                return _("on {date}").format(
                    date=df_start.format(DAY_MONTH_YEAR_FORMAT)
                )
            else:
                if start.year == end.year:
                    if start.month == end.month:
                        if start.day == end.day:
                            return _("on {date}").format(
                                date=df_start.format(DAY_MONTH_YEAR_FORMAT)
                            )
                        else:
                            start_part = df_start.format(DAY_FORMAT)
                            end_part = df_end.format(DAY_MONTH_YEAR_FORMAT)
                            return _("from {start_part} to {end_part}").format(
                                start_part=start_part, end_part=end_part
                            )
                    else:
                        start_part = df_start.format(DAY_MONTH_FORMAT)
                        end_part = df_end.format(DAY_MONTH_YEAR_FORMAT)
                        return _("from {start_part} to {end_part}").format(
                            start_part=start_part, end_part=end_part
                        )
                else:
                    start_part = df_start.format(DAY_MONTH_YEAR_FORMAT)
                    end_part = df_end.format(DAY_MONTH_YEAR_FORMAT)
                    return _("from {start_part} to {end_part}").format(
                        start_part=start_part, end_part=end_part
                    )

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        filters.append("categories")
        return filters
