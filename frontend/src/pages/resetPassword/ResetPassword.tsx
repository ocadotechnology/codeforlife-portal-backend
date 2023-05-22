import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Stack,
  Typography,
  Button
} from '@mui/material';

import {
  getSearchParams,
  stringToProperty
} from 'codeforlife/lib/esm/helpers';

import { paths } from '../../app/router';
import BasePage from '../../pages/BasePage';
import PageSection from '../../components/PageSection';
import ThemedBox from '../../components/ThemedBox';
import {
  Form,
  EmailField,
  SubmitButton
} from 'codeforlife/lib/esm/components/form';

enum UserType {
  teacher = 'teacher',
  independent = 'independent'
}

interface ResetPasswordParams {
  userType: UserType
}

interface ResetPasswordForm {
  email: string;
}

const initialValues: ResetPasswordForm = {
  email: ''
};

const ResetPassword: React.FC = () => {
  const navigate = useNavigate();

  let params = getSearchParams({
    userType: { cast: stringToProperty(UserType) }
  }) as ResetPasswordParams | null;

  React.useEffect(() => {
    if (params === null) {
      navigate(paths.internalServerError);
    }
  }, []);

  if (params === null) return <></>;
  else if (params.userType === undefined) {
    params = null;
    return <></>;
  }

  return (
    <BasePage>
      <PageSection maxWidth='md'>
        <ThemedBox withIcons userType={params.userType}>
          <Stack gap={1}>
            <Typography textAlign='center' variant='h4'>
              Reset password
            </Typography>
            <Typography textAlign='center' variant='h5'>
              Please enter your email address
            </Typography>
            <Typography textAlign='center'>
              We will send an email with a link to reset your password.
            </Typography>
            <Form
              initialValues={initialValues}
              onSubmit={(values, { setSubmitting }) => {
                // TODO: Connect this to the backend
                console.log(values);
                setSubmitting(false);
              }}
            >
              <EmailField
                placeholder='Email address'
                helperText='Enter your email address'
                required
              />
              <Stack direction='row' gap={5} justifyContent='center'>
                <Button
                  className='cancel'
                  onClick={() => { navigate(-1); }}
                >
                  Cancel
                </Button>
                <SubmitButton>
                  Reset password
                </SubmitButton>
              </Stack>
            </Form>
          </Stack>
        </ThemedBox>
      </PageSection>
    </BasePage>
  );
};

export default ResetPassword;
