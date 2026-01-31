from django.db.models import Q
from django.utils import timezone


upcoming_events_query = (
    (
        Q(post__extension__event_end_date__isnull=True)
        & Q(post__extension__event_start_date__gte=timezone.now())
    )
    | (
        Q(post__extension__event_end_date__isnull=False)
        & Q(post__extension__event_end_date__gte=timezone.now())
    )
    | (  # Include events that have upcoming occurrences
        Q(post__extension__recurrences__isnull=False)
        & Q(post__extension__recurrences_end_date__gte=timezone.now())
    )
)

past_events_query = (
    Q(post__extension__event_end_date__isnull=True)
    & Q(post__extension__event_start_date__lt=timezone.now())
) | (
    Q(post__extension__event_end_date__isnull=False)
    & Q(post__extension__event_end_date__lt=timezone.now())
)


def add_recurrent_posts(qs, reverse=False, after=None):
    """Return a list containing all posts from the given quersyet and a clone post
    for each post that have recurring occurrences.
    """
    posts_with_recurrences = []

    for post_content in qs:
        if post_content.post.extension.exists():
            post_event = post_content.post.extension.first()
            if post_event.recurrences:
                posts_with_recurrences.extend(post_event.get_post_occurrences(after))
            else:
                # If this post has no recurrences, add the post to the list
                posts_with_recurrences.append(post_content)

    def get_sort_key(item):
        # Sort first by is_pinned (True comes first), then by date
        is_pinned = not item.post.extension.first().is_pinned
        start_date = getattr(
            item, "occurrence", item.post.extension.first().event_start_date
        )
        return (is_pinned, start_date)

    posts_with_recurrences.sort(key=get_sort_key, reverse=reverse)
    return posts_with_recurrences


def is_infinite_recurrence(recurrences) -> bool:
    return any([rule.count is rule.until is None for rule in recurrences.rrules])
