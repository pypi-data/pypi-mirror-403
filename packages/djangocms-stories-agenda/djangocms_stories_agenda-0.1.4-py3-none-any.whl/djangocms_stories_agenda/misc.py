def get_inline_instances(self, request, obj=None):
    from django.conf import settings
    from djangocms_stories.admin import PostAdmin
    from djangocms_stories.models import Post, StoriesConfig

    from .admin import PostExtensionInline

    inline_instances = super(PostAdmin, self).get_inline_instances(request, obj)

    if request.resolver_match.url_name == "djangocms_stories_post_add":
        # get app config from POST request
        if request.POST.get("app_config"):
            app_config = StoriesConfig.objects.get(
                pk=int(request.POST.get("app_config"))
            )
        elif request.GET.get("app_config"):
            app_config = StoriesConfig.objects.get(
                pk=int(request.GET.get("app_config"))
            )
    elif request.resolver_match.url_name == "djangocms_stories_post_change":
        # get app config from Post object
        post = Post.objects.get(pk=request.resolver_match.kwargs["object_id"])
        app_config = post.app_config

    # get template_prefix from config
    template_prefix = app_config.template_prefix
    if template_prefix == "djangocms_stories_agenda" or (
        getattr(settings, "DJANGOCMS_STORIES_AGENDA_TEMPLATE_PREFIXES", False)
        and template_prefix in settings.DJANGOCMS_STORIES_AGENDA_TEMPLATE_PREFIXES
    ):
        return inline_instances

    return list(
        filter(
            lambda instance: not isinstance(instance, PostExtensionInline),
            inline_instances,
        )
    )
