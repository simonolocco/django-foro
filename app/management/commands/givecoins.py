from django.core.management.base import BaseCommand, CommandError
from app.models import User  # replace 'app' with your app's name

class Command(BaseCommand):
    help = 'Give coins to a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')
        parser.add_argument('amount', type=int, help='Amount of coins to give')

    def handle(self, *args, **options):
        username = options['username']
        amount = options['amount']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')

        user.coins += amount
        user.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully gave {amount} coins to {username}. New total: {user.coins}'))
