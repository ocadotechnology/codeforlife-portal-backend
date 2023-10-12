import api, { useLogoutMutation } from './api';
import {
  useSubscribeToNewsletterMutation,
  useConsentFormMutation
} from './dotmailer';
import {
  useRegisterUserMutation,
  useDownloadStudentPackMutation
} from './home';
import { useLoginMutation } from './login';
import {
  useCreateOrganisationMutation,
  useLeaveOrganisationMutation
} from './organisation';
import {
  useRequestIndependentStudentPasswordResetMutation,
  useRequestTeacherPasswordResetMutation,
  useResetPasswordMutation,
  useVerifyPasswordMutation,
  useDeleteAccountMutation
} from './registration';

import {
  useGetStudentScoreQuery,
  useGetStudentKuronoGameDataQuery,
  useUpdateSchoolStudentDetailsMutation,
  useUpdateStudentDetailsMutation,
  useJoinSchoolRequestMutation,
  useRevokeSchoolRequestMutation,
  useIsRequestingToJoinSchoolQuery
} from './student';
import {
  useGetTeacherDataQuery,
  useInviteTeacherMutation,
  useUpdateSchoolMutation,
  useToggleAdminMutation,
  useOrganisationKickMutation,
  useInviteToggleAdminMutation,
  useResendInviteMutation,
  useDeleteInviteMutation
} from './teacher/dashboard';
import {
  useGetClassQuery,
  useGetStudentsByAccessCodeQuery,
  useUpdateClassMutation,
  useDeleteClassMutation,
  useMoveClassMutation,
  useTeacherHas2faQuery,
  useDisable2faMutation
} from './teacher/teach';
import { useUpdateTeacherAccountDetailsMutation } from './teacher/account';

export default api;
export {
  // api
  useLogoutMutation,
  // dotmailer
  useSubscribeToNewsletterMutation,
  useConsentFormMutation,
  // home
  useRegisterUserMutation,
  useDownloadStudentPackMutation,
  // login
  useLoginMutation,
  // organisation
  useCreateOrganisationMutation,
  useLeaveOrganisationMutation,
  // registration
  useRequestIndependentStudentPasswordResetMutation,
  useRequestTeacherPasswordResetMutation,
  useResetPasswordMutation,
  useVerifyPasswordMutation,
  useDeleteAccountMutation,
  // student
  useGetStudentScoreQuery,
  useGetStudentKuronoGameDataQuery,
  useUpdateStudentDetailsMutation,
  useUpdateSchoolStudentDetailsMutation,
  useJoinSchoolRequestMutation,
  useRevokeSchoolRequestMutation,
  useIsRequestingToJoinSchoolQuery,
  // teacher dashboard
  useGetTeacherDataQuery,
  useInviteTeacherMutation,
  useUpdateSchoolMutation,
  useToggleAdminMutation,
  useOrganisationKickMutation,
  useInviteToggleAdminMutation,
  useResendInviteMutation,
  useDeleteInviteMutation,
  // teacher/teach
  useGetClassQuery,
  useGetStudentsByAccessCodeQuery,
  useUpdateClassMutation,
  useDeleteClassMutation,
  useMoveClassMutation,
  // teacher/account
  useUpdateTeacherAccountDetailsMutation,
  useTeacherHas2faQuery,
  useDisable2faMutation
};
