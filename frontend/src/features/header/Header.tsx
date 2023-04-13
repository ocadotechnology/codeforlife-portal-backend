import React from 'react';
import {
  IconButton,
  Link,
  Button
} from '@mui/material';
import {
  Menu as MenuIcon
} from '@mui/icons-material';

import { ElevatedAppBar, Image } from 'codeforlife/lib/esm/components';

import { paths } from 'app/router';

import CflLogo from 'images/cfl_logo.png';
import OgLogo from 'images/ocado_group.svg';

import LoginSelect from './LoginSelect';
import MenuDrawer from './MenuDrawer';

const Header: React.FC = () => {
  const [menuIsOpen, setMenuIsOpen] = React.useState(false);

  const display = { xs: 'none', sm: 'inline' };
  const mr = { sm: 1, md: 4 };

  return (
    <>
      <ElevatedAppBar props={{ color: 'white' }}>
        <Image
          alt='Code for Life'
          src={CflLogo}
          boxProps={{ maxWidth: '60px' }}
          href={paths.home}
        />
        <Image
          alt='Ocado Group'
          src={OgLogo}
          boxProps={{
            maxWidth: '100px',
            mx: { xs: 'auto', ...mr }
          }}
          href={process.env.REACT_APP_OCADO_GROUP_HREF}
          hrefInNewTab
        />
        <Link sx={{ display, mr }} href={paths.teachers}>
          Teachers
        </Link>
        <Link sx={{ display, mr }} href={paths.students} color='secondary'>
          Students
        </Link>
        <Button sx={{ display, mr, ml: 'auto' }} href={paths.register}>
          Register
        </Button>
        <LoginSelect sx={{ display, width: '200px' }} />
        <IconButton
          onClick={() => { setMenuIsOpen(true); }}
          sx={{ display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>
      </ElevatedAppBar>
      <MenuDrawer isOpen={menuIsOpen} setIsOpen={setMenuIsOpen} />
    </>
  );
};

export default Header;
