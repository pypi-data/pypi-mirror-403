// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import { DASFProgressReport } from '@dasf/dasf-messaging';
import Paper from '@mui/material/Paper';
import ReportItemContent from './ReportItemContent';
import Box from '@mui/material/Box';

function ReportItem({ reportItem }: { reportItem: DASFProgressReport }) {
  return (
    <Box sx={{ my: 2 }}>
      <Paper elevation={3}>
        <Box sx={{ p: 2 }}>
          <ReportItemContent reportItem={reportItem} />
        </Box>
      </Paper>
    </Box>
  );
}

export default ReportItem;
