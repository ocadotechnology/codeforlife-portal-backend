import React from 'react';
import {
  SwipeableDrawer,
  Stack,
  Button,
  Link,
  LinkProps,
  Typography,
  useTheme
} from '@mui/material';

import { paths } from '../../app/router';

import { insertDividerBetweenElements } from 'codeforlife/lib/esm/helpers';

const MenuDrawer: React.FC<{
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}> = ({ isOpen, setIsOpen }) => {
  const theme = useTheme();

  const accordionDetailLinks: LinkProps[] = [
    { children: 'Student' },
    { children: 'Teacher' },
    { children: 'Independent' }
  ];
  const links: LinkProps[] = [
    {
      children: 'Teachers',
      href: paths.teacher._,
      color: theme.palette.primary.main
    },
    {
      children: 'Students',
      href: paths.student._,
      color: theme.palette.secondary.main
    },
    { children: 'About us', href: paths.aboutUs._ },
    { children: 'Help and support', href: '' },
    { children: 'Cookie settings', href: '' },
    { children: 'Privacy notice', href: paths.privacyNotice._ },
    { children: 'Terms of use', href: paths.termsOfUse._ },
    { children: 'Get involved', href: paths.getInvolved._ }
  ];

  return (
    <SwipeableDrawer
      anchor="right"
      open={isOpen}
      onClose={() => {
        setIsOpen(false);
      }}
      onOpen={() => {
        setIsOpen(true);
      }}
    >
      <Stack sx={{ mx: 4, my: 2 }} spacing={5}>
        <Button style={{ width: '100%' }} href={paths.register._}>
          Register
        </Button>
        <Stack
          spacing={1}
          padding={1}
          border={`2px solid ${theme.palette.tertiary.main}`}
        >
          <Typography
            color={theme.palette.tertiary.main}
            style={{ textShadow: '1px 1px 1px rgba(0, 0, 0, 0.5)' }}
            fontWeight="bold"
            variant="body2"
          >
            Log in
          </Typography>
          {insertDividerBetweenElements({
            elements: accordionDetailLinks.map((linkProps, index) => (
              <Link key={index} {...linkProps} color="Black" />
            )),
            dividerProps: {
              sx: {
                borderColor: theme.palette.tertiary.main
              }
            }
          })}
        </Stack>
        <Stack spacing={1}>
          {insertDividerBetweenElements({
            elements: links.map((linkProps, index) => (
              <Link
                key={index}
                {...linkProps}
                color={
                  linkProps.color === undefined ? 'Black' : linkProps.color
                }
              />
            ))
          })}
        </Stack>
      </Stack>
    </SwipeableDrawer>
  );
};

export default MenuDrawer;
