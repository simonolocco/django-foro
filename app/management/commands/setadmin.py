from django.core.management.base import BaseCommand
from app.models import User  # adjust import path if needed

class Command(BaseCommand):
    help = 'Give or revoke admin rights to a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('--set', action='store_true', help='Make user admin')
        parser.add_argument('--unset', action='store_true', help='Remove admin rights')

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['username'])
            if options['set']:
                user.is_staff = True
                user.is_superuser = True
                user.is_admin = True      # <--- Set custom admin flag here
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Admin rights given to {user.username}"))
            elif options['unset']:
                user.is_staff = False
                user.is_superuser = False
                user.is_admin = False     # <--- Unset custom admin flag here
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Admin rights removed from {user.username}"))
            else:
                self.stdout.write(self.style.ERROR("Specify --set or --unset"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("User not found"))
