from django.core.management.base import BaseCommand

from post.services.category_service import remove_uncategorized_category


class Command(BaseCommand):
    help = "Sets category to NULL for all posts in 'Uncategorized' category and deletes the 'Uncategorized' category."

    def handle(self, *args, **options):
        result = remove_uncategorized_category()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {result['updated_posts']} post(s) to category=NULL "
                f"and deleted {result['deleted_categories']} 'Uncategorized' category record(s)."
            )
        )
