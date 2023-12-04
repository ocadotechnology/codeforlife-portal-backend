from datetime import timedelta
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import status

from common import email_messages
from common.helpers.emails import (
    INVITE_FROM,
    NOTIFICATION_EMAIL,
    DotmailerUserType,
    add_to_dotmailer,
    generate_token,
    send_email,
    update_email,
)
from common.helpers.generators import get_random_username, generate_access_code
from common.models import (
    Class,
    JoinReleaseStudent,
    SchoolTeacherInvitation,
    Student,
    Teacher,
)
from common.permissions import check_teacher_authorised, logged_in_as_teacher
from common.utils import using_two_factor

from game.level_management import levels_shared_with, unshare_level

from portal.forms.invite_teacher import InviteTeacherForm
from portal.forms.organisation import OrganisationForm
from portal.forms.registration import DeleteAccountForm
from portal.forms.teach import (
    ClassCreationForm,
    InvitedTeacherForm,
    TeacherAddExternalStudentForm,
    TeacherEditAccountForm,
)
from portal.helpers.decorators import ratelimit
from portal.helpers.password import check_update_password
from portal.helpers.ratelimit import (
    RATELIMIT_LOGIN_GROUP,
    RATELIMIT_LOGIN_RATE,
    RATELIMIT_METHOD,
    clear_ratelimit_cache_for_user,
)

from two_factor.utils import devices_for_user

from .teach import create_class, teacher_view_class


@login_required(login_url=reverse_lazy("teacher_login"))
def get_students_from_access_code(request, access_code):
    student_class = Class.objects.get(access_code=access_code)
    check_teacher_authorised(request, student_class.teacher)
    students_query = Student.objects.filter(
        class_field__access_code=access_code
    )
    # TODO: make this into a method for the student so we can reuse it
    students = [
        {
            "id": student.id,
            "class_field": getattr(student.class_field, "id", 0),
            "new_user": {
                "id": getattr(student.new_user, "id", 0),
                "first_name": getattr(student.new_user, "first_name", ""),
                "last_name": getattr(student.new_user, "last_name", ""),
            },
            "pending_class_request": getattr(
                student.pending_class_request, "id", 0
            ),
            "blocked_time": student.blocked_time.strftime("%Y-%m-%d %H:%M:%S")
            if student.blocked_time
            else "",
        }
        for student in students_query
        if student.new_user.is_active
    ]

    return JsonResponse({"students_per_access_code": students})


def get_student_details(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    try:
        student_class = Class.objects.get(
            access_code=student.class_field.access_code
        )
        check_teacher_authorised(request, student_class.teacher)
    except (ObjectDoesNotExist, AttributeError) as error:
        return JsonResponse({"error": str(error)})
    # TODO: make this into a method for the student so we can reuse it
    return JsonResponse(
        {
            "student": {
                "id": student.id,
                "class_field": getattr(student.class_field, "id", 0),
                "new_user": {
                    "id": getattr(student.new_user, "id", 0),
                    "first_name": getattr(student.new_user, "first_name", ""),
                    "last_name": getattr(student.new_user, "last_name", ""),
                },
                "pending_class_request": getattr(
                    student.pending_class_request, "id", 0
                ),
                "blocked_time": student.blocked_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if student.blocked_time
                else "",
            }
        }
    )


def _get_update_account_rate(group, request):
    """
    Custom rate which checks in a POST request is performed on the update
    account form on the teacher dashboard. It needs to check if
    "update_account" is in the POST request because there are 2 other forms
    on the teacher dashboard that can also perform POST request, but we
    do not want to ratelimit those.
    :return: the rate used in the decorator below.
    """
    return RATELIMIT_LOGIN_RATE if "update_account" in request.POST else None


def _get_update_account_ratelimit_key(group, request):
    """
    Get the username from the request as a ratelimit cache key.
    :return: the username from the request.
    """
    return request.user.username


@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def dashboard_manage(request):
    teacher = request.user.new_teacher

    if teacher.school:
        return dashboard_teacher_view(request)
    else:
        return JsonResponse(status=200, data={"redirect": "onboarding"})


@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
@ratelimit(
    group=RATELIMIT_LOGIN_GROUP,
    key=_get_update_account_ratelimit_key,
    method=RATELIMIT_METHOD,
    rate=_get_update_account_rate,
    block=True,
)
def dashboard_teacher_view(request):
    teacher = request.user.new_teacher
    school = teacher.school

    teacher_json = {
        "id": teacher.id,
        "is_admin": teacher.is_admin,
        "teacher_first_name": teacher.new_user.first_name,
        "teacher_last_name": teacher.new_user.last_name,
        "teacher_email": teacher.new_user.email,
    }

    school_json = {
        "name": school.name,
        "postcode": school.postcode,
        "country": school.country.name,
    }

    coworkers = (
        Teacher.objects.filter(school=school)
        .values(
            "id",
            is_teacher_admin=F("is_admin"),
            teacher_first_name=F("new_user__first_name"),
            teacher_last_name=F("new_user__last_name"),
            teacher_email=F("new_user__email"),
        )
        .order_by("teacher_last_name", "teacher_first_name")
    )
    coworkers_json = list(coworkers)
    [
        coworkers_json.insert(0, coworkers_json.pop(i))
        for i in range(len(coworkers_json))
        if coworkers_json[i]["teacher_email"] == teacher.new_user.email
    ]

    sent_invites = (
        SchoolTeacherInvitation.objects.filter(school=school).values(
            "id",
            "invited_teacher_first_name",
            "invited_teacher_last_name",
            "invited_teacher_email",
            "invited_teacher_is_admin",
            "expiry",
            "token",
        )
        if teacher.is_admin
        else []
    )
    sent_invites_json = list(sent_invites)

    backup_tokens = check_backup_tokens(request)

    classes = []
    classes_json = []
    requests = []
    requests_json = []
    if teacher.is_admin:
        # Making sure the current teacher classes come up first
        classes = school.classes()
        for klass in classes:
            classes_json.append(
                {
                    "name": klass.name,
                    "access_code": klass.access_code,
                    "class_teacher_first_name": klass.teacher.new_user.first_name,
                    "class_teacher_last_name": klass.teacher.new_user.last_name,
                    "class_teacher_id": klass.teacher.id,
                }
            )
        [
            classes_json.insert(0, classes_json.pop(i))
            for i in range(len(classes_json))
            if classes_json[i]["class_teacher_id"] == teacher.id
        ]

        requests = Student.objects.filter(
            pending_class_request__teacher__school=school
        ).values(
            student_id=F("id"),
            student_first_name=F("new_user__first_name"),
            student_email=F("new_user__email"),
            request_class=F("pending_class_request__name"),
            request_teacher_first_name=F(
                "pending_class_request__teacher__new_user__first_name"
            ),
            request_teacher_last_name=F(
                "pending_class_request__teacher__new_user__last_name"
            ),
            request_teacher_email=F(
                "pending_class_request__teacher__new_user__email"
            ),
            request_teacher_id=F("pending_class_request__teacher__id"),
        )
        requests_json = list(requests)
        [
            requests_json.insert(0, requests_json.pop(i))
            for i in range(len(requests_json))
            if requests_json[i]["request_teacher_id"] == teacher.id
        ]

    else:
        classes = Class.objects.filter(teacher=teacher).values(
            "name",
            "access_code",
            class_teacher_first_name=F("teacher__new_user__first_name"),
            class_teacher_last_name=F("teacher__new_user__last_name"),
            class_teacher_id=F("teacher__id"),
        )
        classes_json = list(classes)

        requests = Student.objects.filter(
            pending_class_request__teacher=teacher
        ).values(
            student_id=F("id"),
            student_first_name=F("new_user__first_name"),
            student_email=F("new_user__email"),
            request_class=F("pending_class_request__name"),
            request_teacher_first_name=F(
                "pending_class_request__teacher__new_user__first_name"
            ),
            request_teacher_last_name=F(
                "pending_class_request__teacher__new_user__last_name"
            ),
            request_teacher_email=F(
                "pending_class_request__teacher__new_user__email"
            ),
            request_teacher_id=F("pending_class_request__teacher__id"),
        )
        requests_json = list(requests)

    for i in range(len(requests_json)):
        requests_json[i]["is_request_teacher"] = (
            requests_json[i]["request_teacher_email"] == teacher.new_user.email
        )

    return JsonResponse(
        data={
            "teacher": teacher_json,
            "classes": classes_json,
            "school": school_json,
            "coworkers": coworkers_json,
            "sent_invites": sent_invites_json,
            "requests": requests_json,  # requests is for classes tab
            "backup_tokens": backup_tokens,  # backup_tokens is for account tab
        }
    )


@require_POST
@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def create_new_class(request):
    teacher = request.user.new_teacher

    form_data = request.POST
    class_teacher = None
    try:
        class_teacher = get_object_or_404(Teacher, id=form_data["teacher_id"])
    except:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    created_class = Class.objects.create(
        name=form_data["class"],
        teacher=class_teacher,
        access_code=generate_access_code(),
        classmates_data_viewable=bool(form_data["see_classmates"]),
        created_by=teacher,
    )

    created_class_info = {
        "name": created_class.name,
        "access_code": created_class.access_code,
    }
    return JsonResponse(status=status.HTTP_201_CREATED, data=created_class_info)


@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def update_school(request):
    teacher = request.user.new_teacher
    if teacher.is_admin:
        form_data = request.POST
        school = teacher.school
        school.name = form_data["name"]
        school.postcode = form_data["postcode"].upper()
        school.country = form_data["country"]
        school.save()
        return HttpResponse()
    else:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)


def check_backup_tokens(request):
    backup_tokens = 0
    # For teachers using 2FA, find out how many backup tokens they have
    if using_two_factor(request.user):
        try:
            backup_tokens = request.user.staticdevice_set.all()[
                0
            ].token_set.count()
        except Exception:
            backup_tokens = 0

    return backup_tokens


@login_required(login_url=reverse_lazy("teacher_login"))
def teacher_2fa_handler(request):
    user = request.user
    if request.method == "GET":
        return JsonResponse(
            {"has2fa": TOTPDevice.objects.filter(user=user).exists()}
        )
    elif request.method == "DELETE":
        user_2fa_instances = TOTPDevice.objects.filter(user=user)
        # sometimes the 2fa TOTPDevice can have several instances
        # hence delete them all
        if user_2fa_instances:
            for instance in user_2fa_instances:
                instance.delete()
            return JsonResponse({"has2fa": False})


@login_required(login_url=reverse_lazy("teacher_login"))
def process_update_account_form(request):
    teacher = request.user.new_teacher
    update_account_form = TeacherEditAccountForm(request.user, request.POST)
    changing_email = False
    changing_password = False
    new_email = ""
    if update_account_form.is_valid():
        data = update_account_form.cleaned_data

        # check not default value for CharField
        changing_password = check_update_password(
            update_account_form, teacher.new_user, request, data
        )

        teacher.new_user.first_name = data["first_name"]
        teacher.new_user.last_name = data["last_name"]

        changing_email, new_email = update_email(teacher, request, data)

        teacher.save()
        teacher.new_user.save()

        # Reset ratelimit cache after successful account details update
        clear_ratelimit_cache_for_user(teacher.new_user.username)

        return JsonResponse(
            {"message": "Your account details have been successfully changed."}
        )

    return JsonResponse(
        {"error": update_account_form.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@require_POST
@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def invite_teacher(request):
    teacher = request.user.new_teacher
    school = teacher.school

    invite_teacher_form = InviteTeacherForm(request.POST)
    if invite_teacher_form.is_valid():
        data = invite_teacher_form.cleaned_data
        invited_teacher_first_name = data["teacher_first_name"]
        invited_teacher_last_name = data["teacher_last_name"]
        invited_teacher_email = data["teacher_email"]
        invited_teacher_is_admin = data["make_admin_ticked"] == True

        token = uuid4().hex
        SchoolTeacherInvitation.objects.create(
            token=token,
            school=school,
            from_teacher=teacher,
            invited_teacher_first_name=invited_teacher_first_name,
            invited_teacher_last_name=invited_teacher_last_name,
            invited_teacher_email=invited_teacher_email,
            invited_teacher_is_admin=invited_teacher_is_admin,
            expiry=timezone.now() + timedelta(days=30),
        )
        account_exists = User.objects.filter(
            email=invited_teacher_email
        ).exists()
        message = email_messages.inviteTeacherEmail(
            request, school.name, token, account_exists
        )

        send_email(
            INVITE_FROM,
            [invited_teacher_email],
            message["subject"],
            message["message"],
            message["subject"],
        )

        return JsonResponse(data={"hasError": False, "error": ""})
    else:
        return JsonResponse(
            data={
                "hasError": True,
                "error": list(invite_teacher_form.errors.values())[0][0],
            }
        )


def check_teacher_is_authorised(teacher, user):
    if teacher == user or (teacher.school != user.school or not user.is_admin):
        return False
    else:
        return True


@require_POST
@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def organisation_kick(request, pk):
    teacher = get_object_or_404(Teacher, id=pk)
    user = request.user.new_teacher

    if not check_teacher_is_authorised(teacher, user):
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    classes = Class.objects.filter(teacher=teacher)
    for klass in classes:
        teacher_id = request.POST.get(klass.access_code.lower(), None)
        teacher_id = int(teacher_id) if teacher_id else None
        if teacher_id:
            new_teacher = get_object_or_404(Teacher, id=teacher_id)
            klass.teacher = new_teacher
            klass.save()

    classes = Class.objects.filter(teacher=teacher)
    if classes.exists():
        classes = classes.values(
            "name",
            "access_code",
            class_teacher_first_name=F("teacher__new_user__first_name"),
            class_teacher_last_name=F("teacher__new_user__last_name"),
            class_teacher_id=F("teacher__id"),
        )
        coworkers = (
            Teacher.objects.filter(school=teacher.school)
            .exclude(id=teacher.id)
            .values(
                "id",
                is_teacher_admin=F("is_admin"),
                teacher_first_name=F("new_user__first_name"),
                teacher_last_name=F("new_user__last_name"),
                teacher_email=F("new_user__email"),
            )
        )
        teacher = {
            "id": teacher.id,
            "is_admin": teacher.is_admin,
            "teacher_first_name": teacher.new_user.first_name,
            "teacher_last_name": teacher.new_user.last_name,
            "teacher_email": teacher.new_user.email,
        }

        return JsonResponse(
            data={
                "source": "organisationKick",
                "teacher": teacher,
                "classes": list(classes),
                "coworkers": list(coworkers),
            },
        )

    teacher.school = None
    teacher.save()

    emailMessage = email_messages.kickedEmail(request, user.school.name)

    send_email(
        NOTIFICATION_EMAIL,
        [teacher.new_user.email],
        emailMessage["subject"],
        emailMessage["message"],
        emailMessage["subject"],
    )

    return HttpResponse()


@require_POST
@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def invite_toggle_admin(request, invite_id):
    invite = SchoolTeacherInvitation.objects.filter(id=invite_id)[0]
    invite.invited_teacher_is_admin = not invite.invited_teacher_is_admin
    invite.save()

    if invite.invited_teacher_is_admin:
        emailMessage = email_messages.adminGivenEmail(request, invite.school)
    else:
        emailMessage = email_messages.adminRevokedEmail(request, invite.school)

    send_email(
        NOTIFICATION_EMAIL,
        [invite.invited_teacher_email],
        emailMessage["subject"],
        emailMessage["message"],
        emailMessage["subject"],
    )

    return JsonResponse(
        status=status.HTTP_200_OK,
        data={"isAdminNow": invite.invited_teacher_is_admin},
    )


@require_POST
@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def organisation_toggle_admin(request, pk):
    teacher = get_object_or_404(Teacher, id=pk)
    user = request.user.new_teacher

    if not check_teacher_is_authorised(teacher, user):
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    teacher.is_admin = not teacher.is_admin
    teacher.save()

    if teacher.is_admin:
        email_message = email_messages.adminGivenEmail(
            request, teacher.school.name
        )
    else:
        # Remove access to all levels that are from other teachers' students
        [
            unshare_level(level, teacher.new_user)
            for level in levels_shared_with(teacher.new_user)
            if hasattr(level.owner, "student")
            and not teacher.teaches(level.owner)
        ]
        email_message = email_messages.adminRevokedEmail(
            request, teacher.school.name
        )

    send_email(
        NOTIFICATION_EMAIL,
        [teacher.new_user.email],
        email_message["subject"],
        email_message["message"],
        email_message["subject"],
    )
    return JsonResponse(
        status=status.HTTP_200_OK, data={"isAdminNow": teacher.is_admin}
    )


@login_required(login_url=reverse_lazy("session-expired"))
def resend_invite_teacher(request, token):
    try:
        invite = SchoolTeacherInvitation.objects.get(token=token)
    except SchoolTeacherInvitation.DoesNotExist:
        invite = None
    teacher = request.user.new_teacher

    # auth the user before re-invitation
    if invite is None or teacher.school != invite.school:
        # messages.error(request, "You do not have permission to perform this action or the invite does not exist")
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)
    else:
        invite.expiry = timezone.now() + timedelta(days=30)
        invite.save()
        teacher = Teacher.objects.filter(id=invite.from_teacher.id)[0]

        message = email_messages.inviteTeacherEmail(
            request, invite.school, token, not (invite.is_expired)
        )
        send_email(
            INVITE_FROM,
            [invite.invited_teacher_email],
            message["subject"],
            message["message"],
            message["subject"],
        )
    return HttpResponse()


@login_required(login_url=reverse_lazy("session-expired"))
def delete_teacher_invite(request, token):
    try:
        invite = SchoolTeacherInvitation.objects.get(token=token)
    except SchoolTeacherInvitation.DoesNotExist:
        invite = None
    teacher = request.user.new_teacher

    # auth the user before deletion
    if invite is None or teacher.school != invite.school:
        # messages.error(request, "You do not have permission to perform this action or the invite does not exist")
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)
    else:
        invite.anonymise()
    return HttpResponse()


@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def teacher_disable_2FA(request, pk):
    teacher = get_object_or_404(Teacher, id=pk)
    user = request.user.new_teacher

    # check user has authority to change
    if teacher.school != user.school or not user.is_admin:
        raise Http404

    [
        device.delete()
        for device in devices_for_user(teacher.new_user)
        if request.method == "POST"
    ]

    return HttpResponseRedirect(reverse_lazy("dashboard"))


@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def get_student_request_data(request, pk):
    try:
        student = get_object_or_404(Student, id=pk)
    except:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    student_json = {
        "student_username": student.new_user.username,
        "class_name": student.pending_class_request.name,
        "class_access_code": student.pending_class_request.access_code,
    }
    students = (
        Student.objects.filter(class_field=student.pending_class_request)
        .order_by("new_user__first_name")
        .values_list("new_user__first_name", flat=True)
    )
    students_json = list(students)

    return JsonResponse(
        data={"student": student_json, "students": students_json}
    )


@require_POST
@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def teacher_accept_student_request(request, pk):
    try:
        student = get_object_or_404(Student, id=pk)
        check_student_request_can_be_handled(request, student)
    except Http404:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    form = TeacherAddExternalStudentForm(
        student.pending_class_request, request.POST
    )
    if form.is_valid():
        data = form.cleaned_data
        student.class_field = student.pending_class_request
        student.pending_class_request = None
        student.new_user.username = get_random_username()
        student.new_user.first_name = data["name"]
        student.new_user.last_name = ""
        student.new_user.email = ""

        student.save()
        student.new_user.save()
        student.new_user.userprofile.save()

        # log the data
        joinrelease = JoinReleaseStudent.objects.create(
            student=student, action_type=JoinReleaseStudent.JOIN
        )
        joinrelease.save()

        return HttpResponse()
    else:
        error = form.errors["name"][0]
        return JsonResponse(
            status=status.HTTP_400_BAD_REQUEST, data={"error": error}
        )


def check_student_request_can_be_handled(request, student):
    """
    Check student is awaiting decision on request
    """
    if not student.pending_class_request:
        raise Http404

    # check user (teacher) has authority to accept student
    check_teacher_authorised(request, student.pending_class_request.teacher)


@require_POST
@login_required(login_url=reverse_lazy("session-expired"))
@user_passes_test(
    logged_in_as_teacher, login_url=reverse_lazy("session-expired")
)
def teacher_reject_student_request(request, pk):
    try:
        student = get_object_or_404(Student, id=pk)
        check_student_request_can_be_handled(request, student)
    except Http404:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    emailMessage = email_messages.studentJoinRequestRejectedEmail(
        request,
        student.pending_class_request.teacher.school.name,
        student.pending_class_request.access_code,
    )
    send_email(
        NOTIFICATION_EMAIL,
        [student.new_user.email],
        emailMessage["subject"],
        emailMessage["message"],
        emailMessage["subject"],
    )

    student.pending_class_request = None
    student.save()

    return HttpResponse()


def invited_teacher(request, token):
    error_message = process_teacher_invitation(request, token)

    if request.method == "POST":
        invited_teacher_form = InvitedTeacherForm(request.POST)
        if invited_teacher_form.is_valid():
            messages.success(
                request,
                "Your account has been created successfully, please log in.",
            )
            return HttpResponseRedirect(reverse_lazy("session-expired"))
    else:
        invited_teacher_form = InvitedTeacherForm()

    return render(
        request,
        "portal/teach/invited.html",
        {
            "invited_teacher_form": invited_teacher_form,
            "error_message": error_message,
        },
    )


def process_teacher_invitation(request, token):
    try:
        invitation = SchoolTeacherInvitation.objects.get(
            token=token, expiry__gt=timezone.now()
        )
    except SchoolTeacherInvitation.DoesNotExist:
        return "Uh oh, the Invitation does not exist or it has expired. 😞"

    if User.objects.filter(email=invitation.invited_teacher_email).exists():
        return (
            "It looks like an account is already registered with this email address. You will need to delete the "
            "other account first or change the email associated with it in order to proceed. You will then be able to "
            "access this page."
        )
    else:
        if request.method == "POST":
            invited_teacher_form = InvitedTeacherForm(request.POST)
            if invited_teacher_form.is_valid():
                data = invited_teacher_form.cleaned_data
                invited_teacher_password = data["teacher_password"]
                newsletter_ticked = data["newsletter_ticked"]

                # Create the teacher
                invited_teacher = Teacher.objects.factory(
                    first_name=invitation.invited_teacher_first_name,
                    last_name=invitation.invited_teacher_last_name,
                    email=invitation.invited_teacher_email,
                    password=invited_teacher_password,
                )
                invited_teacher.is_admin = invitation.invited_teacher_is_admin
                invited_teacher.school = invitation.school
                invited_teacher.invited_by = invitation.from_teacher
                invited_teacher.save()

                # Verify their email
                generate_token(invited_teacher.new_user, preverified=True)

                # Add to Dotmailer if they ticked the box
                if newsletter_ticked:
                    user = invited_teacher.user.user
                    add_to_dotmailer(
                        user.first_name,
                        user.last_name,
                        user.email,
                        DotmailerUserType.TEACHER,
                    )

                # Anonymise the invitation
                invitation.anonymise()
