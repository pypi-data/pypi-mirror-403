from isapilib.api.models import BranchAPI
from isapilib.management.commands._base_create_model import BaseCreateModelCommand


class Command(BaseCreateModelCommand):
    Model = BranchAPI
