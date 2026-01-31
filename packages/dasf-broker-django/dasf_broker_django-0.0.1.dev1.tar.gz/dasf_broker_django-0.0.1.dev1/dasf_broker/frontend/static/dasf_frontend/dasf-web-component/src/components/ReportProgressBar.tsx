// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import { DASFProgressReport, Status } from '@dasf/dasf-messaging';

function ReportProgressBar({ report }: { report: DASFProgressReport }) {
  const childCount =
    typeof report.children === 'undefined'
      ? 0
      : report.children.filter(
          (childReport) => childReport.status == Status.Success,
        ).length;
  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Box sx={{ minWidth: 100 }}>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            Step {childCount} of {report.steps}
          </Typography>
        </Box>
        <Box sx={{ width: '100%', ml: 1 }}>
          <LinearProgress
            variant="determinate"
            value={(childCount / report.steps) * 100}
          />
        </Box>
      </Box>
      {typeof report.children != 'undefined' && report.children.length > 0 && (
        <Box sx={{ width: '100%', ml: 1, m: 1 }}>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            {report.children[report.children.length - 1].status ==
              Status.Running && <CircularProgress size="1rem" sx={{ mr: 2 }} />}
            {report.children[report.children.length - 1].step_message}
          </Typography>
        </Box>
      )}
    </>
  );
}

export default ReportProgressBar;
