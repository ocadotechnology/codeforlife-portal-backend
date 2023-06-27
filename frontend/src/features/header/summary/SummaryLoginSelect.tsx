import React from 'react';
import {
  Select,
  SelectProps,
  MenuItem,
  outlinedInputClasses,
  selectClasses,
  MenuItemProps,
  SvgIconProps,
  SvgIcon,
  svgIconClasses,
  Box
} from '@mui/material';

import { wrap } from 'codeforlife/lib/esm/helpers';
import typography from 'codeforlife/lib/esm/theme/typography';
import { secondary } from 'codeforlife/lib/esm/theme/colors';

type SvgIconElement = React.ReactElement<SvgIconProps, typeof SvgIcon>;

export interface SummaryLoginSelectProps extends Pick<SelectProps, (
  'sx' |
  'IconComponent'
)> {
  rotateIcon?: boolean;
  width: string;
  text: string;
  menuItemsProps: Array<MenuItemProps & {
    icon: SvgIconElement;
    children: string;
  }>;
}

const SummaryLoginSelect: React.FC<SummaryLoginSelectProps> = ({
  sx,
  IconComponent,
  rotateIcon = false,
  width,
  text,
  menuItemsProps
}) => {
  const [open, setOpen] = React.useState(false);

  return (
    <Select
      open={open}
      onOpen={() => { setOpen(true); }}
      onClose={() => { setOpen(false); }}
      IconComponent={IconComponent}
      displayEmpty
      value=''
      MenuProps={{ style: { width } }}
      sx={{
        ...sx,
        width,
        height: '42px',
        ':hover': {
          textDecoration: 'underline'
        },
        [`.${selectClasses.outlined}`]: {
          ...typography.button,
          padding: '6px 38px 6px 16px !important',
          whiteSpace: 'pre',
          overflowWrap: 'break-word'
        },
        ...(!rotateIcon && {
          [`.${selectClasses.iconOpen}`]: {
            transform: 'none'
          }
        }),
        [`.${svgIconClasses.root}`]: {
          color: typography.body1?.color,
          position: 'absolute',
          right: '16px'
        },
        [`.${outlinedInputClasses.notchedOutline}`]: {
          border: `2px solid ${secondary[500]} !important`
        }
      }}
    >
      <MenuItem value='' style={{ display: 'none' }}>
        {text}
      </MenuItem>
      {menuItemsProps.map(({
        icon,
        children,
        onClick,
        sx,
        ...otherMenuItemProps
      }, index) =>
        <MenuItem
          key={index}
          onClick={wrap({
            before: () => { setOpen(false); }
          }, onClick)}
          sx={{
            ...sx,
            fontSize: '14px !important',
            margin: 0,
            padding: '6px 12px 6px 16px',
            border: `2px solid ${secondary[500]}`,
            borderTop: 'none',
            ':hover': {
              textDecoration: 'underline',
              backgroundColor: 'transparent'
            }
          }}
          {...otherMenuItemProps}
        >
          {children}
          <Box marginLeft='auto'>
            {icon}
          </Box>
        </MenuItem>
      )}
    </Select>
  );
};

export default SummaryLoginSelect;
