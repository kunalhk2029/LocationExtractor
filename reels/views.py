from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ReelUploadForm
from .models import ReelJob
from .processing import ProcessingError, process_job


def index(request):
    jobs = ReelJob.objects.order_by("-created_at")[:50]
    return render(request, "reels/index.html", {"jobs": jobs})


def upload(request):
    if request.method == "POST":
        form = ReelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save()
            messages.success(request, "Upload complete. You can process the reel now.")
            return redirect(reverse("reels-detail", kwargs={"job_id": job.id}))
    else:
        form = ReelUploadForm()
    return render(request, "reels/upload.html", {"form": form})


def detail(request, job_id: int):
    job = get_object_or_404(ReelJob, pk=job_id)
    return render(request, "reels/detail.html", {"job": job})


def process(request, job_id: int):
    if request.method != "POST":
        return redirect(reverse("reels-detail", kwargs={"job_id": job_id}))

    job = get_object_or_404(ReelJob, pk=job_id)
    try:
        process_job(job)
        messages.success(request, "Processing complete.")
    except ProcessingError as exc:
        messages.error(request, f"Processing failed: {exc}")
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f"Unexpected error: {exc}")
    return redirect(reverse("reels-detail", kwargs={"job_id": job_id}))
