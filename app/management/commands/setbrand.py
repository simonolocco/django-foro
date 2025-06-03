from django.core.management.base import BaseCommand, CommandError
from app.models import User  # Replace with the correct import path

class Command(BaseCommand):
    help = 'Set a user as a brand'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to mark as brand')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        try:
            user = User.objects.get(username=username)
            user.is_brand = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"User '{username}' is now marked as a brand."))
        except User.DoesNotExist:
            raise CommandError(f"User with username '{username}' does not exist.")
