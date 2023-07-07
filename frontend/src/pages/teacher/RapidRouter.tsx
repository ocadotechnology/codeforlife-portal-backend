import React from 'react';
import {
  Button,
  Link,
  Typography
} from '@mui/material';
import {
  ChevronRight as ChevronRightIcon,
  OpenInNew as OpenInNewIcon
} from '@mui/icons-material';
import { paths } from '../../app/router';
import TeacherSection from './TeacherSection';

const RapidRouter: React.FC = () => {
  return (
    <TeacherSection
      videoSource={process.env.REACT_APP_RR_FOR_TEACHER_YOUTUBE_VIDEO_SRC as string}
      direction='row-reverse'
    >
      <Typography variant='h4'>
        Rapid router
      </Typography>
      <Typography>
        Rapid Router is a fun and engaging education resource that helps teach the first principles of computer programming covered in the UK Computing curriculum.
      </Typography>
      <Typography>
        Built on &apos;Blockly&apos;, an easy-to-use visual programming language, Rapid Router enables teachers to monitor and manage individual pupil progress and identify where more support is required.
      </Typography>
      <Typography>
        See how the Rapid Router fits into&nbsp;
        <Link
          href={process.env.REACT_APP_INTRO_TO_CODING_ENGLAND}
          color="inherit"
          underline="always"
          target="_blank"
        >
          English national curriculum — the computer science strand
          <OpenInNewIcon fontSize='small' />
        </Link>
        &nbsp;and&nbsp;
        <Link
          href={process.env.REACT_APP_INTRO_TO_CODING_SCOTLAND}
          color="inherit"
          underline="always"
          target="_blank"
        >
          the Scottish curriculum.
          <OpenInNewIcon fontSize='small' />
        </Link>
      </Typography>
      <Button
        endIcon={<ChevronRightIcon />}
        style={{
          marginTop: 'auto',
          marginLeft: 'auto'
        }}
        href={paths.rapidRouter._}
      >
        Try out Rapid Router
      </Button>
    </TeacherSection>
  );
};

export default RapidRouter;
