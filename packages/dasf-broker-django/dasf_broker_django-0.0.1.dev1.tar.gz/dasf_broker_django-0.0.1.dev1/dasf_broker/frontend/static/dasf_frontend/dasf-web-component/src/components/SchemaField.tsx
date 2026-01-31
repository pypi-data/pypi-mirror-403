// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

// @ts-expect-error: importing React is necessary for react@18.2.0
import React from 'react';
import { FieldProps } from '@rjsf/utils';
import { getDefaultRegistry } from '@rjsf/core';

const {
  fields: { SchemaField },
} = getDefaultRegistry();

const CustomSchemaField = (props: FieldProps) => {
  if (props.schema.uiSchema) {
    const uiSchema = {
      ...(props.uiSchema ? props.uiSchema : {}),
      ...props.schema.uiSchema,
    };
    return <SchemaField {...props} uiSchema={uiSchema} />;
  }
  return <SchemaField {...props} />;
};

export default CustomSchemaField;
