import time
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import all models from JSON data files across all apps."

    IMPORTERS = [
        ("Blog", "blog.services.blog_service", "import_blogs"),
        ("News", "news.services.news_service", "import_news"),
        ("Case Studies", "case_studies.services.case_study_service", "import_case_studies"),
        ("Event Reports", "event_report.services.event_report_service", "import_event_reports"),
        ("Issues", "issue.services.issue_service", "import_issues"),
        ("Publications", "publication.services.publication_service", "import_publications"),
        (
            "Empowerment Programs",
            "empowerment_program.services.empowerment_service",
            "import_empowerment_programs",
        ),
        ("Fellowships", "fellowship.services.fellowship_service", "import_fellowships"),
        ("Team Members", "team.services.team_service", "import_team"),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            nargs="+",
            type=str,
            help="Import only specific apps. Choices: blog, news, case_studies, "
            "event_report, issue, publication, empowerment_program, fellowship, team, post",
        )
        parser.add_argument(
            "--skip-posts",
            action="store_true",
            default=False,
            help="Skip importing posts (which requires a posts.json file).",
        )

    def handle(self, *args, **options):
        only = options.get("only")
        skip_posts = options.get("skip_posts")
        total_start = time.time()
        results = {}
        errors = {}

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Starting Master Import ===\n"))

        for label, module_path, func_name in self.IMPORTERS:
            # Filter by --only if provided
            app_key = module_path.split(".")[0]
            if only and app_key not in only:
                continue

            self.stdout.write(f"  Importing {label}... ", ending="")
            start = time.time()

            try:
                module = __import__(module_path, fromlist=[func_name])
                import_func = getattr(module, func_name)
                result = import_func()
                elapsed = time.time() - start
                results[label] = result
                self.stdout.write(self.style.SUCCESS(f"OK ({elapsed:.2f}s)"))
                self._print_result(result)
            except Exception as e:
                elapsed = time.time() - start
                errors[label] = str(e)
                self.stdout.write(self.style.ERROR(f"FAILED ({elapsed:.2f}s)"))
                self.stderr.write(f"    Error: {e}")
                if options.get("verbosity", 1) >= 2:
                    self.stderr.write(traceback.format_exc())

        # Handle posts separately (different function signature)
        if not skip_posts and (not only or "post" in only):
            self._import_posts(results, errors, options)

        total_elapsed = time.time() - total_start
        self._print_summary(results, errors, total_elapsed)

    def _import_posts(self, results, errors, options):
        self.stdout.write("  Importing Posts... ", ending="")
        start = time.time()

        file_path = settings.BASE_DIR / "posts.json"
        if not file_path.exists():
            elapsed = time.time() - start
            errors["Posts"] = f"posts.json not found at {file_path}"
            self.stdout.write(self.style.WARNING(f"SKIPPED ({elapsed:.2f}s)"))
            self.stderr.write(f"    Warning: posts.json not found at {file_path}")
            return

        try:
            from post.services.post_service import import_posts_from_json

            result = import_posts_from_json(file_path=file_path)
            elapsed = time.time() - start
            results["Posts"] = result
            self.stdout.write(self.style.SUCCESS(f"OK ({elapsed:.2f}s)"))
            self._print_result(result)
        except Exception as e:
            elapsed = time.time() - start
            errors["Posts"] = str(e)
            self.stdout.write(self.style.ERROR(f"FAILED ({elapsed:.2f}s)"))
            self.stderr.write(f"    Error: {e}")
            if options.get("verbosity", 1) >= 2:
                self.stderr.write(traceback.format_exc())

    def _print_result(self, result):
        if isinstance(result, dict):
            for key, value in result.items():
                self.stdout.write(f"    {key}: {value}")

    def _print_summary(self, results, errors, total_elapsed):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n=== Import Complete ({total_elapsed:.2f}s) ===\n"))
        self.stdout.write(f"  Successful: {len(results)}")
        self.stdout.write(f"  Failed:     {len(errors)}")

        if errors:
            self.stdout.write(self.style.ERROR("\n  Failed imports:"))
            for label, error in errors.items():
                self.stdout.write(self.style.ERROR(f"    - {label}: {error}"))

        self.stdout.write("")
