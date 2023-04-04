import React from 'react';
import {
  Unstable_Grid2 as Grid,
  GridDirection,
  Stack,
  Typography
} from '@mui/material';

import { Image } from 'codeforlife/lib/esm/components';
import { ResponsiveStyleValue } from '@mui/system';

const Introduction: React.FC<{
  header: string,
  img: { alt: string, src: string },
  children: React.ReactNode,
  direction?: ResponsiveStyleValue<GridDirection>
}> = ({ header, img, children, direction = 'row' }) => {
  return <>
    <Grid
      container
      spacing={{ xs: 2, lg: 3 }}
      padding={{ xs: 1, md: 2, lg: 3 }}
      display='flex'
      direction={direction}
    >
      <Grid xs={12} md={6}>
        <Stack sx={{ height: '100%' }}>
          <Typography variant='h5' py={1}>
            {header}
          </Typography>
          {children}
        </Stack>
      </Grid>
      <Grid xs={12} md={6} className='flex-center'>
        <Image
          alt={img.alt}
          src={img.src}
          boxProps={{ sx: { maxWidth: '550px' } }}
        />
      </Grid>
    </Grid >
  </>;
};

export default Introduction;