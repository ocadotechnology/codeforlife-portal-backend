import { createApi } from '@reduxjs/toolkit/query/react';

import baseQuery from './baseQuery';

const api = createApi({
  reducerPath: 'api',
  baseQuery,
  endpoints: () => ({})
});

export default api;
