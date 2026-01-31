// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import { Status } from '@dasf/dasf-messaging';
import CircularProgress from '@mui/material/CircularProgress';
import DoneIcon from '@mui/icons-material/Done';
import { pink } from '@mui/material/colors';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';

function StepMessage({ status, message }: { status: Status; message: string }) {
  return (
    <span>
      {status == Status.Running && (
        <CircularProgress size="1rem" sx={{ mr: 2 }} />
      )}
      {status == Status.Success && <DoneIcon color="success" sx={{ mr: 1 }} />}
      {status == Status.Error && (
        <ReportProblemIcon sx={{ color: pink[500], mr: 1 }} />
      )}
      {message}
    </span>
  );
}

export default StepMessage;
