import api from './api';
import {
  useSubscribeToNewsletterMutation,
  useConsentFormMutation
} from './endpoints/dotmailer';
import {
  useRegisterUserMutation,
  useLogoutUserMutation,
  useDownloadStudentPackMutation
} from './endpoints/home';
import {
  useLoginTeacherMutation,
  useLoginDependentStudentMutation,
  useLoginDependentStudentDirectlyMutation,
  useLoginIndependentStudentMutation
} from './endpoints/login';
import {
  useRequestIndependentStudentPasswordResetMutation,
  useRequestTeacherPasswordResetMutation,
  useResetPasswordMutation,
  useDeleteAccountMutation
} from './endpoints/registration';

export default api;
export {
  // dotmailer
  useSubscribeToNewsletterMutation,
  useConsentFormMutation,
  // home
  useRegisterUserMutation,
  useLogoutUserMutation,
  useDownloadStudentPackMutation,
  // login
  useLoginTeacherMutation,
  useLoginDependentStudentMutation,
  useLoginDependentStudentDirectlyMutation,
  useLoginIndependentStudentMutation,
  // registration
  useRequestIndependentStudentPasswordResetMutation,
  useRequestTeacherPasswordResetMutation,
  useResetPasswordMutation,
  useDeleteAccountMutation
};
