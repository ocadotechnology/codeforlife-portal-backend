import {
  Grid,
  Typography,
  Button,
  useTheme,
  InputAdornment
} from '@mui/material';
import DashboardBanner from './DashboardBanner';
import DashboardHeader from './DashboardHeader';
import BasePage from '../BasePage';
import React from 'react';
import {
  Add,
  Business,
  Create,
  DeleteOutline,
  DoDisturbOnOutlined,
  DoNotDisturb,
  EmailOutlined,
  PersonOutlined
} from '@mui/icons-material';
import { INVITE_TEACHER_SCHEMA, SCHOOL_DETAILS_UPDATE_SCHEMA } from './schemas';
import { INVITE_TEACHER_INITIAL_VALUES } from './constants';
import CflTable, {
  CflTableBody,
  CflTableCellElement
} from '../../components/CflTable';
import { getSchool, getTeachersData, getUser } from './dummyMethods';
import {
  TextField,
  CheckboxField,
  AutocompleteField
} from 'codeforlife/lib/esm/components/form';
import { getNames } from 'country-list';
import { CflHorizontalForm } from '../../components/formik/CflForm';
import PageSection from '../../components/PageSection';

const InviteTeacherForm: React.FC = (): JSX.Element => {
  const theme = useTheme();
  return (
    <CflHorizontalForm
      header="Invite a teacher to your school"
      initialValues={INVITE_TEACHER_INITIAL_VALUES}
      validationSchema={INVITE_TEACHER_SCHEMA}
      onSubmit={(values) => {
        alert(JSON.stringify(values, null, 2));
      }}
      submitButton={
        <Button type="submit">
          Invite teacher
        </Button>
      }
    >
      <TextField
        placeholder="First name of teacher"
        helperText="Enter first name of teacher"
        name="teacherFirstName"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <PersonOutlined />
            </InputAdornment>
          )
        }}
      />
      <TextField
        placeholder="Teacher's last name"
        helperText="Enter the teacher's last name"
        name="teacherLastName"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <PersonOutlined />
            </InputAdornment>
          )
        }}
      />
      <TextField
        placeholder="Teacher's email"
        helperText="Enter the teacher's email"
        name="teacherEmail"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <EmailOutlined />
            </InputAdornment>
          )
        }}
      />
      <CheckboxField
        name="isAdmin"
        sx={{ color: theme.palette.info.dark }}
        stackProps={{
          justifyContent: 'flex-start'
        }}
        formControlLabelProps={{
          label: 'Make an administrator of the school'
        }}
      />
    </CflHorizontalForm>
  );
};

const UpdateSchoolDetailsForm: React.FC = (): JSX.Element => {
  const { schoolName, schoolPostcode, schoolCountry } = getSchool();
  return (
    <CflHorizontalForm
      header="Update details of your school or club"
      subheader="Update your school or club's name and/or postcode"
      initialValues={{
        schoolCountry,
        schoolPostcode,
        schoolName
      }}
      validationSchema={SCHOOL_DETAILS_UPDATE_SCHEMA}
      onSubmit={(values) => {
        alert(JSON.stringify(values, null, 2));
      }}
      submitButton={
        <Button type="submit">
          Update details
        </Button>
      }
    >
      <TextField
        placeholder="Name of school or club"
        helperText="Enter your school's name"
        name="schoolName"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <Business />
            </InputAdornment>
          )
        }}
      />
      <TextField
        placeholder="Postcode / Zipcode"
        helperText="Enter your school's postcode"
        name="schoolPostcode"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <Business />
            </InputAdornment>
          )
        }}
      />
      <AutocompleteField
        options={getNames()}
        textFieldProps={{
          name: 'schoolCountry',
          helperText: "Enter your school's country",
          placeholder: 'Country'
        }}
      />
    </CflHorizontalForm>
  );
};

const TeachersTableActions: React.FC<{
  teacherEmail: string;
  userEmail: string;
  isTeacherAdmin: boolean;
  twoFactorAuthentication?: boolean;
}> = ({
  teacherEmail,
  userEmail,
  isTeacherAdmin,
  twoFactorAuthentication
}): JSX.Element => {
  if (teacherEmail === userEmail) {
    return (
      <>
        <Button endIcon={<Create />}>
          Update details
        </Button>
        {/* This button below will be used for pending invites  */}
        <Button endIcon={<EmailOutlined />}>
          Resend invite
        </Button>
      </>
    );
  } else if (isTeacherAdmin) {
    return (
      <>
        <Button color="error" endIcon={<DoNotDisturb />}>
          Revoke admin
        </Button>
        <Button color="error" endIcon={<DeleteOutline />}>
          Delete
        </Button>
      </>
    );
  } else {
    return (
      <>
        <Button endIcon={<Add />}>Make admin </Button>
        <Button endIcon={<DoDisturbOnOutlined />} color="error">
          Disable 2FA
        </Button>
      </>
    );
  }
};

const TeachersTable: React.FC = (): JSX.Element => {
  const { email } = getUser();
  const teachersData = getTeachersData();
  const youText = (
    <Typography variant="body2" fontWeight="bold">
      (you)
    </Typography>
  );

  return (
    <CflTable titles={['Name', 'Administrator status', 'Actions']}>
      {teachersData.map(
        ({ teacherName, isTeacherAdmin, teacherEmail }, keyIdx: number) => (
          <CflTableBody key={`${keyIdx}`}>
            <CflTableCellElement>
              <Typography variant="subtitle1">
                {teacherName} {teacherEmail === email ? youText : ''}{' '}
              </Typography>
            </CflTableCellElement>
            <CflTableCellElement
              direction="column"
              alignItems="flex-start"
              justifyContent="flex-start"
            >
              <Typography variant="subtitle1">
                {isTeacherAdmin ? 'Teacher Administrator' : 'Standard Teacher'}
              </Typography>
              <Typography variant="subtitle1">({teacherEmail}) </Typography>
            </CflTableCellElement>
            <CflTableCellElement justifyContent="center">
              <TeachersTableActions
                {...{
                  teacherEmail,
                  userEmail: email,
                  isTeacherAdmin
                }}
              />
            </CflTableCellElement>
          </CflTableBody>
        )
      )}
    </CflTable>
  );
};
const TeacherSchool: React.FC = (): JSX.Element => {
  const { schoolName, accessCode } = getSchool();
  const theme = useTheme();
  return (
    <BasePage>
      <DashboardBanner />
      <DashboardHeader page="Your school" />
      <PageSection>
        <Typography align="center" variant="h4">
          Your school: {schoolName} ({accessCode})
        </Typography>
        <Typography align="left">
          As an administrator of your school or club, you can select other
          teachers to whom you can provide or revoke administrative rights. You
          can also add and remove teachers from your school or club. As
          administrator, you have the ability to see and amend other
          teachers&apos; classes. Please bear this in mind when assigning admin
          rights to other teachers.
        </Typography>
      </PageSection>
      <PageSection>
        <InviteTeacherForm />
      </PageSection>
      <PageSection>
        <Typography variant="h5">
          These teachers are already part of your school or club
        </Typography>
        <TeachersTable />
      </PageSection>
      <PageSection>
        <Grid container>
          <Grid item sm={6}>
            <Typography>
              Select &apos;Delete&apos; to delete a teacher from your school or
              club. You will be able to move any existing classes assigned to
              that teacher to other teachers in your school or club.
            </Typography>
          </Grid>
          <Grid item sm={6}>
            <Typography fontWeight="bold" color="error">
              We strongly recommend that administrators who are using 2FA ensure
              there is another administrator who will be able to disable their
              2FA should they have problems with their smartphone or tablet.
            </Typography>
          </Grid>
        </Grid>
      </PageSection>
      <PageSection bgcolor={theme.palette.info.main}>
        <UpdateSchoolDetailsForm />
      </PageSection>
    </BasePage>
  );
};

export default TeacherSchool;
