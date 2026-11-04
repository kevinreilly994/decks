"""Blocking scheduler that runs sync_roster on an interval (APScheduler).

APScheduler is optional (requirements-prod). For most deployments prefer the OS
scheduler (cron / Windows Task Scheduler) invoking `manage.py sync_roster`.
"""
from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run sync_roster on a schedule (default: daily). Blocking process."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24)
        parser.add_argument("--run-now", action="store_true")

    def handle(self, *args, **opts):
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.interval import IntervalTrigger
        except ImportError:
            self.stderr.write(
                "APScheduler not installed. Run `pip install APScheduler`, or "
                "schedule `manage.py sync_roster` via cron / Windows Task Scheduler."
            )
            return

        def job():
            call_command("sync_roster")

        if opts["run_now"]:
            job()

        scheduler = BlockingScheduler()
        scheduler.add_job(job, IntervalTrigger(hours=opts["hours"]), id="sync_roster")
        self.stdout.write(self.style.SUCCESS(
            f"Scheduler started: every {opts['hours']}h. Ctrl-C to stop."
        ))
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
