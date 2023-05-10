import React from 'react';
import { useNavigate } from 'react-router-dom';

import {
  getSearchParams,
  stringToBoolean
} from 'codeforlife/lib/esm/helpers';

import SadFaceImg from '../../images/sadface.png';
import PaperPlaneImg from '../../images/paper_plane.png';
import { paths } from '../../app/router';
import BasePage from '../../pages/BasePage';
import PageSection from '../../components/PageSection';
import Status from './Status';

const EmailVerification: React.FC = () => {
  const navigate = useNavigate();

  const params = getSearchParams({
    success: stringToBoolean,
    forTeacher: stringToBoolean
  });

  React.useEffect(() => {
    if (params === null) {
      navigate(paths.internalServerError);
    }
  }, []);

  return (
    <BasePage>
      <PageSection maxWidth='md' className='flex-center'>
        {params !== null && (params.success
          ? <Status
            forTeacher={params.forTeacher}
            header='We need to verify your email address'
            body={[
              'An email has been sent to the address you provided.',
              'Please follow the link within the email to verify your details. This will expire in 1 hour.',
              'If you don\'t receive the email within the next few minutes, check your spam folder.'
            ]}
            imageProps={{
              alt: 'PaperPlane',
              src: PaperPlaneImg
            }}
          />
          : <Status
            forTeacher={params.forTeacher}
            header='Your email address verification failed'
            body={[
              'You used an invalid link, either you mistyped the URL or that link is expired.',
              'When you next attempt to log in, you will be sent a new verification email.'
            ]}
            imageProps={{
              alt: 'SadFace',
              src: SadFaceImg
            }}
          />
        )}
      </PageSection>
    </BasePage>
  );
};

export default EmailVerification;