import logging

from cards.models.combatant import Combatant
from cards.models.privacy_policy import PrivacyPolicy
from cards.utility.decorators import permission_required
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from feature_switches.helpers import is_enabled

logger = logging.getLogger("cards")


@require_http_methods(["GET", "POST"])
def privacy_policy(request, code=None):
    """View the privacy policy, optionally with UUID for accepting it.

    Args:
        code: Code for a Combatant's privacy_acceptance_code field
    """
    combatant = None
    code = request.POST.get("code", code)
    if code is not None:
        combatant = get_object_or_404(Combatant, privacy_acceptance_code=code)

    latest = PrivacyPolicy.latest_version()
    if latest:
        policy_text = latest.text.replace("[DATE]", latest.created_at.strftime("%Y-%m-%d"))
    else:
        policy_text = ""
    context = {"policy": policy_text}
    if request.method == "POST":
        if combatant is None:
            return HttpResponseBadRequest()

        if "accept" in request.POST:
            if is_enabled("pin_authentication", user=combatant):
                combatant.accept_privacy_policy(send_email=False)
                pin_code = combatant.one_time_codes.create_pin_setup_code()
                return redirect("pin-setup", code=pin_code.code)

            combatant.accept_privacy_policy()
            context = {
                "card_url": combatant.card_url,
                "sent_email": True,
                "is_new_combatant": True,
            }
            return render(request, "home/registration_completed.html", context)

        if "decline" in request.POST:
            combatant.delete()
            return render(request, "privacy/privacy_declined.html", {})

        return HttpResponseBadRequest()

    context["code"] = code if combatant is not None else None
    if combatant is not None:
        logger.debug("privacy acceptance for combatant %s", combatant)

    return render(request, "privacy/privacy_policy.html", context)


@permission_required("can_edit_privacy_policy")
@csrf_protect
@require_http_methods(["GET", "POST"])
def edit_privacy_policy(request):
    """Edit or create a privacy policy draft."""
    draft = PrivacyPolicy.objects.filter(approved=False).first()
    latest = PrivacyPolicy.latest_version()

    if request.method == "POST":
        if "create_draft" in request.POST:
            if draft:
                return redirect("edit-privacy-policy")

            if not latest:
                context = {
                    "draft": None,
                    "latest": None,
                    "error": "No approved policy exists to create a draft from.",
                }
                return render(request, "privacy/edit_policy.html", context)

            draft = PrivacyPolicy(
                text=latest.text, changelog="", approved=False
            )
            try:
                draft.save()
                logger.info("Created privacy policy draft from latest %s", draft.draft_uuid)
                return redirect("edit-privacy-policy")
            except ValidationError as e:
                context = {
                    "draft": None,
                    "latest": latest,
                    "error": str(e),
                }
                return render(request, "privacy/edit_policy.html", context)

        if "delete_draft" in request.POST:
            if draft:
                draft_uuid = draft.draft_uuid
                draft.delete()
                logger.info("Deleted privacy policy draft %s", draft_uuid)
            return redirect("edit-privacy-policy")

        text = request.POST.get("text", "").strip()
        changelog = request.POST.get("changelog", "").strip()

        if not text:
            context = {
                "draft": draft,
                "latest": latest,
                "error": "Policy text is required.",
                "text": text,
                "changelog": changelog,
            }
            if draft:
                draft_url = request.build_absolute_uri(
                    reverse("view-draft", args=[draft.draft_uuid])
                )
                context["draft_url"] = draft_url
            return render(request, "privacy/edit_policy.html", context)

        if draft:
            draft.text = text
            draft.changelog = changelog
            try:
                draft.save()
                logger.info("Updated privacy policy draft %s", draft.draft_uuid)
            except ValidationError as e:
                context = {
                    "draft": draft,
                    "latest": latest,
                    "error": str(e),
                    "text": text,
                    "changelog": changelog,
                }
                draft_url = request.build_absolute_uri(
                    reverse("view-draft", args=[draft.draft_uuid])
                )
                context["draft_url"] = draft_url
                return render(request, "privacy/edit_policy.html", context)

        draft_url = request.build_absolute_uri(
            reverse("view-draft", args=[draft.draft_uuid])
        )
        context = {
            "draft": draft,
            "latest": latest,
            "draft_url": draft_url,
            "text": draft.text,
            "changelog": draft.changelog,
            "saved": True,
        }
        return render(request, "privacy/edit_policy.html", context)

    latest_text = ""
    if latest:
        latest_text = latest.text.replace("[DATE]", latest.created_at.strftime("%Y-%m-%d"))

    context = {
        "draft": draft,
        "latest": latest,
        "latest_text": latest_text,
        "text": draft.text if draft else latest_text,
        "changelog": draft.changelog if draft else "",
    }
    if draft:
        draft_url = request.build_absolute_uri(
            reverse("view-draft", args=[draft.draft_uuid])
        )
        context["draft_url"] = draft_url

    return render(request, "privacy/edit_policy.html", context)


@require_http_methods(["GET"])
def view_draft(request, draft_uuid):
    """Public view of a draft privacy policy."""
    draft = PrivacyPolicy.get_draft_by_uuid(draft_uuid)
    if not draft:
        return render(
            request,
            "message/message.html",
            {"message": "Draft not found."},
            status=404,
        )

    if draft.approved:
        if draft.version:
            return redirect("view-version", version=draft.version)
        return redirect("privacy-policy")

    context = {
        "draft": draft,
        "policy": draft.text,
        "changelog": draft.changelog,
    }
    return render(request, "privacy/view_draft.html", context)


@permission_required("can_edit_privacy_policy")
@csrf_protect
@require_http_methods(["POST"])
def approve_policy(request, draft_uuid):
    """Approve a draft privacy policy."""
    draft = PrivacyPolicy.get_draft_by_uuid(draft_uuid)
    if not draft:
        return render(
            request,
            "message/message.html",
            {"message": "Draft not found."},
            status=404,
        )

    if draft.approved:
        if draft.version:
            return redirect("view-version", version=draft.version)
        return redirect("privacy-policy")

    try:
        draft.approve()
        logger.info("Approved privacy policy draft %s as version %s", draft_uuid, draft.version)
        return redirect("view-version", version=draft.version)
    except ValidationError as e:
        return render(
            request,
            "message/message.html",
            {"message": f"Error approving policy: {str(e)}"},
            status=400,
        )


@require_http_methods(["GET"])
def view_version(request, version):
    """View a specific version of the privacy policy."""
    policy = get_object_or_404(PrivacyPolicy, version=version, approved=True)
    latest = PrivacyPolicy.latest_version()
    is_latest = latest and latest.version == version

    policy_text = policy.text.replace("[DATE]", policy.created_at.strftime("%Y-%m-%d"))

    context = {
        "policy": policy,
        "policy_text": policy_text,
        "changelog": policy.changelog,
        "is_latest": is_latest,
        "latest_version": latest.version if latest else None,
    }
    return render(request, "privacy/view_version.html", context)
