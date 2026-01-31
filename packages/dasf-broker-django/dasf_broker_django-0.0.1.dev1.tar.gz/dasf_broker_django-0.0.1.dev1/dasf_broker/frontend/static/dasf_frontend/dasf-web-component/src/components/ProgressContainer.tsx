// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

// @ts-expect-error: importing React is necessary for react@18.2.0
import React, { useState } from 'react';
import ReportProgressBar from './ReportProgressBar';
import { DASFProgressReport } from '@dasf/dasf-messaging';
import ReportItems from './ReportItems';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';

function ProgressContainer({ report }: { report: DASFProgressReport }) {
  const [showChildren, setShowChildren] = useState<boolean>(false);

  return (
    <>
      <ReportProgressBar report={report} />
      {typeof report.children != 'undefined' && (
        <>
          <Button variant="text" onClick={() => setShowChildren(!showChildren)}>
            Show details
          </Button>
          <Collapse in={showChildren} timeout="auto" unmountOnExit>
            <ReportItems children={report.children} />
          </Collapse>
        </>
      )}
    </>
  );
}

export default ProgressContainer;
