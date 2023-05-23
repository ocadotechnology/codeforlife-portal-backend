import React from 'react';
import BasePage from '../BasePage';
import DashboardBanner from './DashboardBanner';
import DashboardHeader from './DashboardHeader';
import {
  Button,
  InputAdornment,
  Stack,
  Typography,
  useTheme
} from '@mui/material';
import {
  DELETE_ACCOUNT_INITIAL_VALUES,
  UPDATE_TEACHER_ACCOUNT_INITIAL_VALUES
} from './constants';
import {
  DELETE_ACCOUNT_SCHEMA,
  UPDATE_TEACHER_ACCOUNT_SCHEMA
} from './schemas';
import {
  DeleteOutline,
  EmailOutlined,
  LockOutlined,
  SecurityOutlined
} from '@mui/icons-material';
import { getUser } from './dummyMethods';
import { TextField, CheckboxField } from 'codeforlife/lib/esm/components/form';
import { CflHorizontalForm } from '../../components/formik/CflForm';
import PageSection from '../../components/PageSection';

const TwoFactorAuthentication: React.FC = (): JSX.Element => {
  return (
    <Stack>
      <Typography variant="h5">Two factor authentication</Typography>
      <Typography>
        Use your smartphone or tablet to enhance your accont&apos;s security by
        using an authenticator app.
      </Typography>
      <Button variant="contained" color="tertiary">
        Setup two factor authentication
      </Button>
    </Stack>
  );
};

const YourAccountForm: React.FC = () => {
  const { firstName, lastName } = getUser();
  return (
    <CflHorizontalForm
      initialValues={{
        ...UPDATE_TEACHER_ACCOUNT_INITIAL_VALUES,
        firstName,
        lastName
      }}
      validationSchema={UPDATE_TEACHER_ACCOUNT_SCHEMA}
      onSubmit={(values) => {
        alert(JSON.stringify(values, null, 2));
      }}
      submitButton={<Button variant="contained">Update details</Button>}
    >
      <TextField
        name="firstName"
        helperText="Enter your first name"
        placeholder="First name"
      />
      <TextField
        placeholder="Last name"
        helperText="Enter your last name"
        name="lastName"
      />
      <TextField
        placeholder="New email address (optional)"
        helperText="Enter your new email address (optional)"
        name="newEmail"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <EmailOutlined />
            </InputAdornment>
          )
        }}
      />
      <TextField
        placeholder="New password (optional)"
        helperText="Enter your new password (optional)"
        name="newPassword"
        type="password"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <SecurityOutlined />
            </InputAdornment>
          )
        }}
      />
      <TextField
        placeholder="Confirm new password (optional)"
        helperText="Confirm your new password (optional)"
        name="confirmPassword"
        type="password"
      />
      <TextField
        placeholder="Current password"
        helperText="Enter your current password"
        name="currentPassword"
        type="password"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <LockOutlined />
            </InputAdornment>
          )
        }}
      />
    </CflHorizontalForm>
  );
};

const DeleteAccountForm: React.FC = (): JSX.Element => {
  const theme = useTheme();
  return (
    <CflHorizontalForm
      header="Delete account"
      subheader="If you no longer wish to have a Code for Life account, you can delete it by confirming below. You will receive an email to confirm this decision."
      subheaderBold="This can't be reversed. All classes you've created will be permanently erased."
      initialValues={DELETE_ACCOUNT_INITIAL_VALUES}
      validationSchema={DELETE_ACCOUNT_SCHEMA}
      onSubmit={(formik, { setSubmitting }) => {
        alert(JSON.stringify(formik, null, 2));
        setSubmitting(false);
      }}
      submitButton={
        <Button
          variant="contained"
          color="error"
          type="submit"
          endIcon={<DeleteOutline />}
        >
          Delete account
        </Button>
      }
    >
      <TextField
        name="currentPassword"
        label="Current password"
        helperText="Enter your current password"
        type="password"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <SecurityOutlined />
            </InputAdornment>
          )
        }}
      />
      <CheckboxField
        name="removeFromNewsletter"
        sx={{ color: theme.palette.info.dark }}
        stackProps={{
          justifyContent: 'flex-start'
        }}
        formControlLabelProps={{
          label:
            'Please remove me from the newsletter and marketing emails too.'
        }}
      />
    </CflHorizontalForm>
  );
};

const TeacherAccount: React.FC = (): JSX.Element => {
  const theme = useTheme();
  return (
    <BasePage>
      <DashboardBanner />
      <DashboardHeader page="Your account" />
      <PageSection>
        <Typography align="center" variant="h4">
          Your account
        </Typography>
        <Typography>You can update your account details below.</Typography>
      </PageSection>
      <PageSection>
        <YourAccountForm />
      </PageSection>
      <PageSection bgcolor={theme.palette.info.main}>
        <TwoFactorAuthentication />
      </PageSection>
      <PageSection>
        <DeleteAccountForm />
      </PageSection>
    </BasePage>
  );
};

export default TeacherAccount;
