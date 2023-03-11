import logging

from django.core.management.base import BaseCommand, CommandParser
from users.services import add_users_from_json

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import referal users from json"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path_to_json")

    def handle(self, *args, **options):
        add_users_from_json(options["path_to_json"])
        log.info("Done")
