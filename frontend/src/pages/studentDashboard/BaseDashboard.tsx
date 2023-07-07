import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  useTheme,
  Link
} from '@mui/material';
import * as yup from 'yup';

import Page from 'codeforlife/lib/esm/components/page';
import { tryValidateSync } from 'codeforlife/lib/esm/helpers/yup';
import { SectionProps as PageSectionProps } from 'codeforlife/lib/esm/components/page/Section';

import Games from './Games';
import RapidRouterProgress from './RapidRouterProgress';
import KuronoProgress from './KuronoProgress';
import StudentAccount from './account/StudentAccount';
import JoinSchool from './joinSchool/JoinSchool';
import Characters from '../../features/characters/Characters';
import { paths } from '../../app/router';

export interface BaseDashboardProps {
  isDependent: boolean;
}

const BaseDashboard: React.FC<BaseDashboardProps> = ({
  isDependent
}) => {
  const theme = useTheme();
  const navigate = useNavigate();

  const params = tryValidateSync(
    useParams(),
    yup.object({
      view: yup.string()
        .oneOf([
          'account',
          'join'
        ] as const)
    })
  );

  // TODO: get from api store.
  const name = 'John';
  const classCode = 1;

  React.useEffect(() => {
    if (params?.view === 'join' && isDependent) {
      navigate(paths.error.forbidden._);
    }
  }, [params]);

  let view: React.ReactElement<PageSectionProps, typeof Page.Section> | undefined;
  switch (params?.view) {
    case 'account':
      view = <StudentAccount isDependent={isDependent} />;
      break;
    case 'join':
      view = <JoinSchool />;
      break;
  }

  return <>
    <Page.Banner
      header={`Welcome, ${name}`}
      subheader={(view === undefined) ? 'This is where you can access your games' : ''}
      textAlign='center'
      bgcolor={isDependent ? 'tertiary' : 'secondary'}
    />
    {view !== undefined
      ? view
      : <>
        <Page.Notification bgcolor={isDependent ? 'tertiary' : 'secondary'}>
          {isDependent
            ? <>You are logged in to class: {classCode}</>
            : <>
              You are logged in as an independent student.
              If you want to join a school, you need to&nbsp;
              <Link onClick={() => { navigate(paths.student.dashboard.independent.joinSchool._); }} color="inherit">
                request to join one
              </Link>
              .
            </>
          }
        </Page.Notification>
        <Page.Section>
          <Games isDependent={isDependent} />
        </Page.Section>
        <Page.Section gridProps={{ bgcolor: theme.palette.info.main }}>
          <RapidRouterProgress isDependent={isDependent} />
        </Page.Section>
        <Page.Section>
          <KuronoProgress isDependent={isDependent} />
        </Page.Section>
        {!isDependent &&
          <Page.Section gridProps={{ bgcolor: theme.palette.info.main }} >
            <Characters game='kurono' />
          </Page.Section>
        }
      </>
    }
  </>;
};

export default BaseDashboard;
