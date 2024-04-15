# pylint: skip-file

# from datetime import timedelta
# from unittest.mock import patch, Mock, ANY

# from common.helpers.emails import NOTIFICATION_EMAIL
# from common.models import UserProfile, Student, Teacher
# from common.tests.utils.classes import create_class_directly
# from common.tests.utils.organisation import create_organisation_directly
# from common.tests.utils.student import (
#     create_school_student_directly,
#     create_independent_student_directly,
# )
# from common.tests.utils.teacher import signup_teacher_directly
# from django.contrib.auth.models import User
# from django.urls import reverse
# from django.utils import timezone

# from . import CronTestCase
# from ....emails import NOTIFICATION_EMAIL
# from ....views.cron import USER_DELETE_UNVERIFIED_ACCOUNT_DAYS


# class TestUser(CronTestCase):
#     # TODO: use fixtures
#     def setUp(self):
#         teacher_email, _ = signup_teacher_directly(preverified=False)
#         create_organisation_directly(teacher_email)
#         _, _, access_code = create_class_directly(teacher_email)
#         _, _, student = create_school_student_directly(access_code)
#         indy_email, _, _ = create_independent_student_directly()

#         self.teacher_user = User.objects.get(email=teacher_email)
#         self.teacher_user_profile = UserProfile.objects.get(
#             user=self.teacher_user
#         )

#         self.indy_user = User.objects.get(email=indy_email)
#         self.indy_user_profile = UserProfile.objects.get(user=self.indy_user)

#         self.student_user: User = student.new_user

#     def send_verify_email_reminder(
#         self,
#         days: int,
#         is_verified: bool,
#         view_name: str,
#         send_email: Mock,
#         assert_called: bool,
#     ):
#         self.teacher_user.date_joined = timezone.now() - timedelta(
#             days=days, hours=12
#         )
#         self.teacher_user.save()
#         self.student_user.date_joined = timezone.now() - timedelta(
#             days=days, hours=12
#         )
#         self.student_user.save()
#         self.indy_user.date_joined = timezone.now() - timedelta(
#             days=days, hours=12
#         )
#         self.indy_user.save()

#         self.teacher_user_profile.is_verified = is_verified
#         self.teacher_user_profile.save()
#         self.indy_user_profile.is_verified = is_verified
#         self.indy_user_profile.save()

#         self.client.get(reverse(view_name))

#         if assert_called:
#             send_email.assert_any_call(
#                 sender=NOTIFICATION_EMAIL,
#                 recipients=[self.teacher_user.email],
#                 subject=ANY,
#                 title=ANY,
#                 text_content=ANY,
#                 replace_url=ANY,
#             )

#             send_email.assert_any_call(
#                 sender=NOTIFICATION_EMAIL,
#                 recipients=[self.indy_user.email],
#                 subject=ANY,
#                 title=ANY,
#                 text_content=ANY,
#                 replace_url=ANY,
#             )

#             # Check only two emails are sent - the student should never be included.
#             assert send_email.call_count == 2
#         else:
#             send_email.assert_not_called()

#         send_email.reset_mock()

#     @patch("portal.views.cron.user.send_email")
#     def test_first_verify_email_reminder_view(self, send_email: Mock):
#         self.send_verify_email_reminder(
#             days=6,
#             is_verified=False,
#             view_name="first-verify-email-reminder",
#             send_email=send_email,
#             assert_called=False,
#         )
#         self.send_verify_email_reminder(
#             days=7,
#             is_verified=False,
#             view_name="first-verify-email-reminder",
#             send_email=send_email,
#             assert_called=True,
#         )
#         self.send_verify_email_reminder(
#             days=7,
#             is_verified=True,
#             view_name="first-verify-email-reminder",
#             send_email=send_email,
#             assert_called=False,
#         )
#         self.send_verify_email_reminder(
#             days=8,
#             is_verified=False,
#             view_name="first-verify-email-reminder",
#             send_email=send_email,
#             assert_called=False,
#         )

#     @patch("portal.views.cron.user.send_email")
#     def test_second_verify_email_reminder_view(self, send_email: Mock):
#         self.send_verify_email_reminder(
#             days=13,
#             is_verified=False,
#             view_name="second-verify-email-reminder",
#             send_email=send_email,
#             assert_called=False,
#         )
#         self.send_verify_email_reminder(
#             days=14,
#             is_verified=False,
#             view_name="second-verify-email-reminder",
#             send_email=send_email,
#             assert_called=True,
#         )
#         self.send_verify_email_reminder(
#             days=14,
#             is_verified=True,
#             view_name="second-verify-email-reminder",
#             send_email=send_email,
#             assert_called=False,
#         )
#         self.send_verify_email_reminder(
#             days=15,
#             is_verified=False,
#             view_name="second-verify-email-reminder",
#             send_email=send_email,
#             assert_called=False,
#         )

#     def test_delete_unverified_accounts_view(self):
#         now = timezone.now()

#         for user in [self.teacher_user, self.indy_user, self.student_user]:
#             user.date_joined = now - timedelta(
#                 days=USER_DELETE_UNVERIFIED_ACCOUNT_DAYS + 1
#             )
#             user.save()

#         for user_profile in [self.teacher_user_profile, self.indy_user_profile]:
#             user_profile.is_verified = True
#             user_profile.save()

#         def delete_unverified_users(
#             days: int,
#             is_verified: bool,
#             assert_exists: bool,
#         ):
#             date_joined = now - timedelta(days=days, hours=12)

#             # Create teacher.
#             teacher_user = User.objects.create(
#                 first_name="Unverified",
#                 last_name="Teacher",
#                 username="unverified.teacher@codeforlife.com",
#                 email="unverified.teacher@codeforlife.com",
#                 date_joined=date_joined,
#             )
#             teacher_user_profile = UserProfile.objects.create(
#                 user=teacher_user,
#                 is_verified=is_verified,
#             )
#             Teacher.objects.create(
#                 user=teacher_user_profile,
#                 new_user=teacher_user,
#                 school=self.teacher_user.new_teacher.school,
#             )

#             # Create dependent student.
#             student_user = User.objects.create(
#                 first_name="Unverified",
#                 last_name="DependentStudent",
#                 username="UnverifiedDependentStudent",
#                 date_joined=date_joined,
#             )
#             student_user_profile = UserProfile.objects.create(
#                 user=student_user,
#             )
#             Student.objects.create(
#                 user=student_user_profile,
#                 new_user=student_user,
#                 class_field=self.student_user.new_student.class_field,
#             )

#             # Create independent student.
#             indy_user = User.objects.create(
#                 first_name="Unverified",
#                 last_name="IndependentStudent",
#                 username="unverified.independentstudent@codeforlife.com",
#                 email="unverified.independentstudent@codeforlife.com",
#                 date_joined=date_joined,
#             )
#             indy_user_profile = UserProfile.objects.create(
#                 user=indy_user,
#                 is_verified=is_verified,
#             )
#             Student.objects.create(
#                 user=indy_user_profile,
#                 new_user=indy_user,
#             )

#             self.client.get(reverse("delete-unverified-accounts"))

#             # Assert the verified users and teach
#             assert User.objects.filter(id=self.teacher_user.id).exists()
#             assert User.objects.filter(id=self.student_user.id).exists()
#             assert User.objects.filter(id=self.indy_user.id).exists()

#             teacher_user_exists = User.objects.filter(
#                 id=teacher_user.id
#             ).exists()
#             indy_user_exists = User.objects.filter(id=indy_user.id).exists()
#             student_user_exists = User.objects.filter(
#                 id=student_user.id
#             ).exists()

#             assert teacher_user_exists == assert_exists
#             assert indy_user_exists == assert_exists
#             assert student_user_exists

#             if teacher_user_exists:
#                 teacher_user.delete()
#             if indy_user_exists:
#                 indy_user.delete()
#             if student_user_exists:
#                 student_user.delete()

#         delete_unverified_users(
#             days=USER_DELETE_UNVERIFIED_ACCOUNT_DAYS - 1,
#             is_verified=False,
#             assert_exists=True,
#         )
#         delete_unverified_users(
#             days=USER_DELETE_UNVERIFIED_ACCOUNT_DAYS,
#             is_verified=False,
#             assert_exists=False,
#         )
#         delete_unverified_users(
#             days=USER_DELETE_UNVERIFIED_ACCOUNT_DAYS,
#             is_verified=True,
#             assert_exists=True,
#         )
#         delete_unverified_users(
#             days=USER_DELETE_UNVERIFIED_ACCOUNT_DAYS + 1,
#             is_verified=False,
#             assert_exists=False,
#         )

# TODO: clean up
