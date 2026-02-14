from django.core.management.base import BaseCommand, CommandError

from reels.models import ReelJob
from reels.processing import process_job


class Command(BaseCommand):
    help = "Process a reel job by ID."

    def add_arguments(self, parser):
        parser.add_argument("job_id", type=int, help="ReelJob ID to process")

    def handle(self, *args, **options):
        job_id = options["job_id"]
        try:
            job = ReelJob.objects.get(pk=job_id)
        except ReelJob.DoesNotExist as exc:
            raise CommandError(f"ReelJob {job_id} not found") from exc

        process_job(job)
        self.stdout.write(self.style.SUCCESS(f"Processed job {job_id}"))
