// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import { DASFProgressReport } from '@dasf/dasf-messaging';
import Box from '@mui/material/Box';
import StepMessage from './StepMessage';

function ReportItemContent({ reportItem }: { reportItem: DASFProgressReport }) {
  return (
    <Box sx={{ ml: 2, my: 1 }}>
      <StepMessage
        status={reportItem.status}
        message={reportItem.step_message}
      />
      {typeof reportItem.children != 'undefined' &&
        reportItem.children.map((child, index) => (
          <ReportItemContent key={index} reportItem={child} />
        ))}
    </Box>
  );
}

export default ReportItemContent;
