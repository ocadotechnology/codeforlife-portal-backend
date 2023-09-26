import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, Typography, useTheme, Link, Stack } from '@mui/material';
import { FieldArray, Form, Formik } from 'formik';

import {
  AutocompleteField
} from 'codeforlife/lib/esm/components/form';
import Page from 'codeforlife/lib/esm/components/page';

import CflTable, {
  CflTableBody,
  CflTableCellElement
} from '../../../components/CflTable';
import { paths } from '../../../app/router';
import { classType, teacherType, useLeaveOrganisationMutation } from '../../../app/api/organisation';
import { moveClassesType, organsationKickType, useOrganisationKickMutation } from '../../../app/api/teacher/dashboard';

const MoveClassTeacherForm: React.FC<{
  source: string;
  classes: classType[];
  teachers: teacherType[];
  teacherId: string;
}> = ({ source, classes, teachers, teacherId }) => {
  interface classFormDataType extends classType {
    newTeacher: string
  };

  interface teacherListType {
    id: number,
    fullName: string
  };

  const theme = useTheme();
  const [leaveOrganisation] = useLeaveOrganisationMutation();
  const [organisationKick] = useOrganisationKickMutation();
  const navigate = useNavigate();

  const onLeaveOrganisation = (info: moveClassesType[]): void => {
    leaveOrganisation(info).unwrap()
      .then(() => {
        navigate(paths.teacher.onboarding._, { state: { leftOrganisation: true } });
      })
      .catch((err) => { console.error('LeaveOrganisation error: ', err); });
  };

  const onOrganisationKick = (info: organsationKickType): void => {
    info.id = teacherId;
    organisationKick(info).unwrap()
      .then(() => {
        navigate(paths.teacher.dashboard.school._, {
          state: {
            message: 'The teacher has been successfully removed from your school or club, and their classes were successfully transferred.'
          }
        });
        navigate(0);
      })
      .catch((err) => { console.error('OrganisationKick error: ', err); });
  };

  // TODO: clean this up
  // initialValues: form value
  // teacherList: for finding newTeacher ID (by findNewTeacherId)
  // teacherOptions: showing form options
  // Data type passed to backend would be {accessCode: newTeacherId} (e.g. {'ab124': '3', 'ab125': '4'})
  const initialValues = classes.map((c: classType) => ({ ...c, newTeacher: '' }));
  const teacherList = teachers.map((t: teacherType) => ({
    id: t.id,
    fullName: `${t.newUserIdFirstName} ${t.newUserIdLastName}`
  }));
  const teacherOptions = teacherList.map((t: teacherListType) => t.fullName);
  const findNewTeacherId = (name: string): number => {
    const selectedTeacher = teacherList.find((t: teacherListType) => (t.fullName === name));
    return selectedTeacher ? (selectedTeacher.id) : -1;
  };

  return (
    <>
      <Typography marginY={theme.spacing(3)}>
        Please specify which teacher you would like the classes below to be moved to.
      </Typography>
      <Formik
        initialValues={initialValues}
        onSubmit={values => {
          const info = Object.create(null);
          values.forEach((v: classFormDataType) => {
            info[v.accessCode.toLowerCase()] = findNewTeacherId(v.newTeacher);
          });
          (source === 'organisationLeave') ? onLeaveOrganisation(info) : onOrganisationKick(info);
        }}
      >
        {() => (
          <Form>
            <FieldArray
              name="classes"
              render={() => (
                <>
                  <CflTable
                    className='body'
                    titles={['Class name', 'New teacher']}
                  >
                    {classes.map((c: classType, index: number) =>
                      <CflTableBody key={c.id}>
                        <CflTableCellElement>
                          <Typography variant="subtitle1">
                            {c.name}
                          </Typography>
                        </CflTableCellElement>
                        <CflTableCellElement
                          direction="column"
                          alignItems="flex-start"
                        >
                          <AutocompleteField
                            options={teacherOptions}
                            textFieldProps={{
                              required: true,
                              name: `${index}.newTeacher`
                            }}
                            freeSolo={true}
                            forcePopupIcon={true}
                            sx={{ width: 200 }}
                          />
                        </CflTableCellElement>
                      </CflTableBody>
                    )}
                  </CflTable >
                  <Stack direction="row" spacing={2}>
                    <Button variant='outlined' onClick={() => {
                      navigate(paths.teacher.dashboard.school._);
                    }}>
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                    >
                      {source === 'organisationKick' ? 'Move classes and remove teacher' : 'Move classes and leave'}
                    </Button>
                  </Stack>
                </>
              )}
            />
          </Form>
        )}
      </Formik>
    </>
  );
};

const MoveClasses: React.FC = () => {
  // TODO: get data from BE
  const userName = 'John Doe';
  const navigate = useNavigate();
  const theme = useTheme();
  const location = useLocation();

  return (
    <>
      <Page.Notification>
        {location.state.source === 'organisationKick'
          ? 'This teacher still has classes assigned to them. You must first move them to another teacher in your school or club.'
          : 'You still have classes, you must first move them to another teacher within your school or club.'
        }
      </Page.Notification>
      <Page.Section>
        <Typography variant="h4" align="center" marginBottom={theme.spacing(5)}>
          Move all classes for teacher {userName}
        </Typography>
        <Link className="back-to" onClick={() => {
          navigate(paths.teacher.dashboard.school._);
        }}>
          dashboard
        </Link>
        <MoveClassTeacherForm
          source={location.state.source}
          classes={location.state.classes}
          teachers={location.state.teachers}
          teacherId={location.state.teacherId}
        />
      </Page.Section >
    </>
  );
};

export default MoveClasses;
