import { PersonOutlined } from '@mui/icons-material';
import { InputAdornment } from '@mui/material';
import { TextField, TextFieldProps } from 'codeforlife/lib/esm/components/form';
import React, { CSSProperties } from 'react';
import * as Yup from 'yup';

const StudentNameField: React.FC<Omit<TextFieldProps, 'name'> & {
  name?: string;
  disabled?: boolean;
  style?: CSSProperties;
}> = ({
  name = 'firstName',
  helperText = 'Choose a name',
  disabled = false,
  style
}) => {
    return (
      <TextField
        required
        name={name}
        helperText={helperText}
        placeholder='Student name'
        validate={Yup
          .string()
          .matches(/^[a-zA-Z0-9-_ ]{1,150}$/gm, 'Name may only contain letters, numbers, dashes, underscores, and spaces.')
        }
        InputProps={{
          style,
          disabled,
          endAdornment: (
            <InputAdornment position="end">
              <PersonOutlined />
            </InputAdornment>
          )
        }}
      />
    );
  };

export default StudentNameField;
