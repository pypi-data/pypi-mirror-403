from django.core.management.base import BaseCommand

from isapilib.api.models import UserAPI, BranchAPI


class Command(BaseCommand):
    help = 'Allow user to connect to database'

    def add_arguments(self, parser):
        parser.add_argument("username", help="Username of user", type=str)
        parser.add_argument("branch", help="Branch api", type=str)

    def handle(self, *args, **options):
        try:
            user = UserAPI.objects.get(username=options['username'])
            branch = BranchAPI.objects.get(pk=options["branch"])

            user.permissions.add(branch)
            self.stdout.write(self.style.SUCCESS(f'{user.username} now can connect to external-{branch.pk}'))
        except UserAPI.DoesNotExist:
            self.stdout.write(self.style.SUCCESS(f"User doesn't exist."))

        except BranchAPI.DoesNotExist:
            self.stdout.write(self.style.SUCCESS(f"Database doesn't exist."))
