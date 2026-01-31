// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import { DASFProgressReport } from '@dasf/dasf-messaging';
import ReportItem from './ReportItem';

function ReportItems({ children }: { children: DASFProgressReport[] }) {
  return (
    <>
      {children.map((child, index) => (
        <ReportItem key={index} reportItem={child} />
      ))}
    </>
  );
}

export default ReportItems;
