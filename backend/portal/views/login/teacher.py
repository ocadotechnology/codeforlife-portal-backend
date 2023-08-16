# from common.models import Teacher
# from django.shortcuts import render
# from two_factor.views import LoginView
# from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

# from portal.forms.teach import TeacherLoginForm
# from portal.views.home import redirect_teacher_to_correct_page
# from . import has_user_lockout_expired

# # This import is required so that 2FA works properly
# from portal import handlers


# class TeacherLoginView(LoginView):
#     template_name = "portal/login/teacher.html"
#     form_list = (
#         ("auth", TeacherLoginForm),
#         ("token", AuthenticationTokenForm),
#         ("backup", BackupTokenForm),
#     )

#     def get_success_url(self):
#         url = self.get_redirect_url()
#         return url or redirect_teacher_to_correct_page(self.request, self.request.user.userprofile.teacher)

#     def post(self, request, *args, **kwargs):
#         """
#         If the email address inputted in the form corresponds to that of a blocked
#         account, this redirects the user to the locked out page. However, if the lockout
#         time is more than 24 hours before this is executed, the account is unlocked.
#         """
#         wizard_step = self.request.POST.get("teacher_login_view-current_step", None)

#         if wizard_step == "auth":
#             email = request.POST.get("auth-username")
#             if Teacher.objects.filter(new_user__email=email).exists():
#                 teacher = Teacher.objects.get(new_user__email=email)

#                 if teacher.blocked_time is not None:
#                     if has_user_lockout_expired(teacher):
#                         teacher.blocked_time = None
#                         teacher.save()
#                     else:
#                         return render(
#                             self.request,
#                             "portal/locked_out.html",
#                             {"is_teacher": True},
#                         )

#         return super(TeacherLoginView, self).post(request, *args, **kwargs)

from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login
from rest_framework import status

from common.models import UserSession


# TODO: fix 2fa and use the above view instead.
def teacher_login_view(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(request, username=username, password=password)
    if user is None:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    # TODO: use google analytics
    UserSession.objects.create(user=user)

    login(request, user)
    return HttpResponse()


# TODO: remove this redirect view and return 401 directly.
def session_expired_view(request: HttpRequest):
    """
    This view is used a temporary solution and should be removed when our auth
    flow is restructured. Django's default behavior with the @login_required
    decorator is to redirect users to the login template found in setting
    LOGIN_URL. Because we're using a React frontend, I want to return a 401
    Unauthorized whenever a user's session cookie expires so we can redirect
    them to the login page. Therefore, all login redirects will direct a to this
    view which will return the desired 401.
    """
    return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
