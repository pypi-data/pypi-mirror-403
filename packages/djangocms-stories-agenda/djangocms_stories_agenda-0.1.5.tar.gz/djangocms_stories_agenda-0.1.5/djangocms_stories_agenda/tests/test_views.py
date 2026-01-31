from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.utils import timezone
from djangocms_stories.cms_appconfig import StoriesConfig, config_defaults
from djangocms_stories.models import Post, PostContent

from djangocms_stories_agenda.models import PostExtension
from djangocms_stories_agenda.views import AgendaArchiveView, AgendaListView


class TestAgendaListView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

        # Create blog config with agenda template prefix
        self.config = StoriesConfig.objects.create(
            **config_defaults,
            namespace="agenda",
            app_title="Agenda",
        )
        self.config.template_prefix = "agenda"
        self.config.save()

        # Create test posts
        now = timezone.now()

        # Past event
        self.past_post = Post.objects.create(
            app_config=self.config,
        )
        self.past_postcontent = PostContent.objects.create(
            post=self.past_post,
            title="Past Event",
            language="en",
        )
        PostExtension.objects.create(
            post=self.past_post, event_start_date=now - timedelta(days=10)
        )

        # Future event
        self.future_post = Post.objects.create(
            app_config=self.config,
        )
        self.future_postcontent = PostContent.objects.create(
            post=self.future_post,
            title="Future Event",
            language="en",
        )
        PostExtension.objects.create(
            post=self.future_post, event_start_date=now + timedelta(days=10)
        )

    def test_agenda_list_view_shows_upcoming_events(self):
        view = AgendaListView()
        view.request = self.request
        view.config = self.config
        view.namespace = self.config.namespace
        view.model = PostContent
        view.kwargs = {"only_upcoming_events": True}

        # Get queryset
        posts = view.get_queryset()

        # Should include future events, but not past events
        self.assertIn(self.future_post.get_content().title, [p.title for p in posts])
        self.assertNotIn(self.past_post.get_content().title, [p.title for p in posts])

        # Check ordering - should be ordered by start date
        event_dates = [p.post.extension.first().event_start_date for p in posts]
        self.assertEqual(event_dates, sorted(event_dates))

    def test_agenda_archive_view_shows_past_events(self):
        view = AgendaArchiveView()
        view.request = self.request
        view.config = self.config
        view.namespace = self.config.namespace
        view.model = PostContent
        view.kwargs = {"only_past_events": True}

        # Get queryset
        posts = view.get_queryset()

        # Should include past events, but not future events
        self.assertIn(self.past_post.get_content().title, [p.title for p in posts])
        self.assertNotIn(self.future_post.get_content().title, [p.title for p in posts])

        # Check ordering - should be ordered by start date in reverse
        event_dates = [p.post.extension.first().event_start_date for p in posts]
        self.assertEqual(event_dates, sorted(event_dates, reverse=True))

    def test_agenda_list_view_shows_ongoing_events(self):
        now = timezone.now()

        # Create an ongoing event (started 10 days ago, ends in 10 days)
        ongoing_post = Post.objects.create(
            app_config=self.config,
        )
        ongoing_postcontent = PostContent.objects.create(  # noqa
            post=ongoing_post,
            title="Ongoing Event",
            language="en",
        )
        ongoing_post.save()

        PostExtension.objects.create(
            post=ongoing_post,
            event_start_date=now - timedelta(days=10),
            event_end_date=now + timedelta(days=10),
        )

        # Initialize view
        view = AgendaListView()
        view.request = self.request
        view.config = self.config
        view.namespace = self.config.namespace
        view.model = PostContent
        view.kwargs = {"only_upcoming_events": True}

        # Get queryset
        posts = view.get_queryset()

        # The ongoing event should be included in upcoming events
        self.assertIn(ongoing_post.get_content().title, [p.title for p in posts])

        # Verify it appears in the correct order (between past and future events)
        event_dates = [p.post.extension.first().event_start_date for p in posts]
        self.assertEqual(event_dates, sorted(event_dates))

    def test_agenda_list_view_pinned_events_first(self):
        now = timezone.now()

        # Create a pinned future event
        pinned_future = Post.objects.create(
            app_config=self.config,
        )
        PostContent.objects.create(
            post=pinned_future, title="Pinned Future Event", language="en"
        )
        PostExtension.objects.create(
            post=pinned_future, event_start_date=now + timedelta(days=5), is_pinned=True
        )

        # Initialize view
        view = AgendaListView()
        view.request = self.request
        view.config = self.config
        view.namespace = self.config.namespace
        view.model = PostContent
        view.kwargs = {"only_upcoming_events": True}

        # Get queryset
        posts_contents = view.get_queryset()
        post_titles = [p.title for p in posts_contents]

        # Pinned event should appear first, followed by other future events
        self.assertEqual(post_titles[0], "Pinned Future Event")
        self.assertIn("Future Event", post_titles[1:])

    def test_agenda_archive_view_pinned_events_not_first(self):
        now = timezone.now()

        # Create a pinned past event
        pinned_past = Post.objects.create(
            app_config=self.config,
        )
        PostContent.objects.create(
            post=pinned_past, title="Pinned Past Event", language="en"
        )
        PostExtension.objects.create(
            post=pinned_past, event_start_date=now - timedelta(days=5), is_pinned=True
        )

        # Initialize view
        view = AgendaArchiveView()
        view.request = self.request
        view.config = self.config
        view.namespace = self.config.namespace
        view.model = PostContent
        view.kwargs = {"only_past_events": True}

        # Get queryset
        posts = view.get_queryset()
        post_titles = [p.title for p in posts]

        # Pinned event should not appear first
        self.assertNotEqual(post_titles[0], "Pinned Past Event")
