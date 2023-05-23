import { boolean, object, ref, string } from 'yup';
import { getNames } from 'country-list';

export const SCHOOL_DETAILS_UPDATE_SCHEMA = object({
  schoolName: string().required('School name is required'),
  schoolPostcode: string().required('School postcode is required'),
  schoolCountry: string()
    .required('School country is required')
    .test('is-country', 'Country is invalid', (value) =>
      getNames().includes(value)
    )
});

export const INVITE_TEACHER_SCHEMA = object({
  teacherFirstName: string().required('First name is required').min(1, 'First name cannot be empty'),
  teacherLastName: string().required('Last name is required').min(1, 'Last name cannot be empty'),
  teacherEmail: string().required('Email is required').email('Email is invalid').min(1, 'Email cannot be empty'),
  isAdmin: boolean().required()
});

export const UPDATE_TEACHER_ACCOUNT_SCHEMA = object({
  firstName: string().required('First name is required'),
  lastName: string().required('Last name is required'),
  newEmailAddress: string().email('Email is invalid'),
  currentPassword: string().required('Current password is required'),
  newPassword: string(),
  confirmPassword: string().oneOf(
    [ref('newPassword'), ''],
    'Passwords must match'
  )
});

export const DELETE_ACCOUNT_SCHEMA = object({
  currentPassword: string().required('Current password is required'),
  removeFromNewsletter: boolean().required()
});

export const CREATE_CLASS_SCHEMA = object({
  className: string().required('Class name is required'),
  teacherName: string().required('Teacher name is required'),
  isStudentProgressVisibleToOthers: boolean().required()
});
