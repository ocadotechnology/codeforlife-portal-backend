import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Button,
  Grid,
  InputAdornment,
  Stack,
  Typography,
  useTheme
} from '@mui/material';
import { LockOutlined, PersonOutline } from '@mui/icons-material';

import Page from 'codeforlife/lib/esm/components/page';
import {
  EmailField,
  Form,
  PasswordField,
  SubmitButton,
  TextField
} from 'codeforlife/lib/esm/components/form';

import DeleteAccountForm from '../../../features/deleteAccountForm/DeleteAccountForm';
import { paths } from '../../../app/router';
import {
  useLogoutUserMutation,
  useUpdateSchoolStudentDetailsMutation,
  useUpdateStudentDetailsMutation
} from '../../../app/api';

const AccountFormPasswordFields: React.FC = () => {
  return (
    <>
      <Grid item xs={12} sm={8}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <PasswordField
            placeholder="New password (optional)"
            helperText="Enter your new password (optional)"
            name="newPassword"
            repeat={[
              {
                name: 'repeatPassword',
                placeholder: 'Confirm new password (optional)',
                helperText: 'Confirm your new password (optional)'
              }
            ]}
          />
        </Stack>
      </Grid>
      <Grid item xs={12} sm={4}>
        <PasswordField
          placeholder="Current password"
          helperText="Enter your current password"
          name="currentPassword"
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <LockOutlined />
              </InputAdornment>
            )
          }}
        />
      </Grid>
    </>
  );
};

const AccountFormButtons: React.FC = () => {
  const navigate = useNavigate();

  return (
    <>
      <Stack direction="row" spacing={2} paddingY={3}>
        <Button
          variant="outlined"
          onClick={() => {
            navigate(-1);
          }}
        >
          Cancel
        </Button>
        <SubmitButton>
          {/* TODO: Connect to backend */}
          Update details
        </SubmitButton>
      </Stack>
    </>
  );
};

const AccountForm: React.FC<{
  isDependent: boolean;
}> = ({ isDependent }) => {
  interface SchoolStudentValues {
    newPassword: string;
    repeatPassword: string;
    currentPassword: string;
  }
  interface IndependentValues extends SchoolStudentValues {
    name: string;
    email: string;
  }

  type Values = SchoolStudentValues | IndependentValues;
  const navigate = useNavigate();

  if (isDependent) {
    // Form complains about the initial values when type
    // does not have name and email
    const initialValues: Values = {
      name: '',
      email: '',
      newPassword: '',
      repeatPassword: '',
      currentPassword: ''
    };

    const [updateSchoolStudent] = useUpdateSchoolStudentDetailsMutation();
    const location = useLocation();
    return (
      <Form
        initialValues={initialValues}
        onSubmit={(values) => {
          const changedPassword =
            'Your account details have been changed successfully. Please login using your new password.';
          updateSchoolStudent(values)
            .unwrap()
            .then(() => {
              navigate(paths.student.dashboard.dependent._, {
                state: {
                  notifications: [
                    {
                      index: 0,
                      props: {
                        children: changedPassword
                      }
                    }
                  ]
                }
              });
            })
            .catch((error) => {
              console.error(error);
              navigate(location.pathname, {
                state: {
                  notifications: [
                    {
                      index: 0,
                      props: {
                        children:
                          'Your password was not changed due to incorrect details'
                      }
                    }
                  ]
                }
              });
            });
        }}
      >
        <Grid container spacing={2}>
          <AccountFormPasswordFields />
        </Grid>
        <AccountFormButtons />
      </Form>
    );
  } else {
    const initialValues: Values = {
      name: '',
      email: '',
      newPassword: '',
      repeatPassword: '',
      currentPassword: ''
    };
    const [updateStudent] = useUpdateStudentDetailsMutation();
    const [logoutUser] = useLogoutUserMutation();
    const location = useLocation();
    return (
      <Form
        initialValues={initialValues}
        onSubmit={(values) => {
          const { email, newPassword, currentPassword, repeatPassword, name } =
            values;
          const isPasswordChanged = [
            newPassword,
            repeatPassword,
            currentPassword
          ].every((el) => el !== '');
          const isEmailChanged = email !== '';
          const isNameChanged = name !== '';
          const notificationMessages: Record<string, boolean> = {
            'Your account details have been changed successfully. Your email will be changed once you have verified it, until then you can still log in with your old email.':
              isEmailChanged,
            'Your account details have been changed successfully. Please login using your new password.':
              isPasswordChanged
          };
          const notifications = Object.keys(notificationMessages)
            .filter((key: string) => notificationMessages[key])
            .map((key: string, idx: number) => {
              return { index: idx, props: { children: key } };
            });

          updateStudent(values)
            .unwrap()
            .then((res) => {
              if (isEmailChanged || isPasswordChanged) {
                logoutUser(null)
                  .unwrap()
                  .then(() => {
                    navigate(paths._, { state: notifications });
                  })
                  .catch(() => {
                    alert('Logout failed.');
                  });
              } else if (isNameChanged) {
                navigate(location.pathname, {
                  state: {
                    notifications: [
                      { index: 0, props: { children: 'Your details have been changed successfully' } }
                    ]
                  }
                });
              }
            })

            .catch((error) => {
              console.error(error);
              navigate(location.pathname, {
                state: {
                  notifications: [
                    {
                      index: 0,
                      props: {
                        children:
                          'Your account was not updated due to incorrect details'
                      }
                    }
                  ]
                }
              });
            });
        }}
      >
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              name="name"
              helperText="Enter your name"
              placeholder="Name"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <PersonOutline />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <EmailField
              placeholder="New email address (optional)"
              helperText="Enter your new email address (optional)"
              name="newEmail"
            />
          </Grid>
          <AccountFormPasswordFields />
        </Grid>
        <AccountFormButtons />
      </Form >
    );
  }
};

const StudentAccount: React.FC<{
  isDependent: boolean;
}> = ({ isDependent }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  return (
    <>
      <Page.Section>
        {isDependent
          ? (
            <>
              <Typography align="center" variant="h4">
                Update your password
              </Typography>
              <Typography>
                You may edit your password below. It must be long enough and hard
                enough to stop your friends guessing it and stealing all of your
                hard work. Choose something memorable though.
              </Typography>
              <Typography>
                If you have any problems, ask a teacher to help you.
              </Typography>
            </>
          )
          : (
            <>
              <Typography align="center" variant="h4">
                Update your account details
              </Typography>
              <Typography>You can update your account details below.</Typography>
              <Typography>
                Please note: If you change your email address, you will need to
                re-verify it. Please ensure your password is strong enough to be
                secure.
              </Typography>
            </>
          )}
        <AccountForm isDependent={isDependent} />
      </Page.Section>
      {!isDependent
        ? (
          <>
            <Page.Section gridProps={{ bgcolor: theme.palette.info.main }}>
              <Typography variant="h5">Join a school or club</Typography>
              <Typography>
                To find out about linking your Code For Life account with a school
                or club, click &apos;Join&apos;.
              </Typography>
              <Button
                onClick={() => {
                  navigate(paths.student.dashboard.independent.joinSchool._);
                }}
              >
                Join
              </Button>
            </Page.Section>
            <Page.Section>
              <DeleteAccountForm userType="independent" />
            </Page.Section>
          </>
        )
        : (
          <></>
        )}
    </>
  );
};

export default StudentAccount;
