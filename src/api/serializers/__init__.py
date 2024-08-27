"""
© Ocado Group
Created on 23/01/2024 at 16:13:13(+00:00).
"""

from .auth_factor import AuthFactorSerializer
from .klass import ReadClassSerializer, WriteClassSerializer
from .school import SchoolSerializer
from .school_teacher_invitation import (
    AcceptSchoolTeacherInvitationSerializer,
    RefreshSchoolTeacherInvitationSerializer,
    SchoolTeacherInvitationSerializer,
)
from .student import (
    CreateStudentSerializer,
    ReleaseStudentSerializer,
    ResetStudentPasswordSerializer,
    TransferStudentSerializer,
)
from .teacher import (
    CreateTeacherSerializer,
    RemoveTeacherFromSchoolSerializer,
    SetSchoolTeacherAdminAccessSerializer,
)
from .user import (
    CreateUserSerializer,
    HandleIndependentUserJoinClassRequestSerializer,
    RegisterEmailToNewsletter,
    RequestUserPasswordResetSerializer,
    ResetUserPasswordSerializer,
    UpdateUserSerializer,
    VerifyUserEmailAddressSerializer,
)
