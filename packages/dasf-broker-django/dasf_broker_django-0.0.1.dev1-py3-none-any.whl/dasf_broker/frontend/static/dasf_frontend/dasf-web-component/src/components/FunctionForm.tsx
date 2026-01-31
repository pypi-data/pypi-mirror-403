// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import Form from '@rjsf/mui';
import { IChangeEvent } from '@rjsf/core';
import {
  RJSFSchema,
  UiSchema,
  RegistryFieldsType,
  RegistryWidgetsType,
} from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

// @ts-expect-error: importing React is necessary for react@18.2.0
import React from 'react';
import { FormEvent } from 'react';

import CustomSchemaField from './SchemaField';

const log = (type: string) => console.log.bind(console, type);

function FunctionForm({
  schema,
  uiSchema,
  fields,
  widgets,
  onSubmit,
  onError,
  onChange,
}: {
  schema?: RJSFSchema;
  uiSchema?: UiSchema;
  fields?: RegistryFieldsType;
  widgets?: RegistryWidgetsType;
  onSubmit?: ({ formData }: IChangeEvent, _event: FormEvent) => void;
  onError?: () => void;
  onChange?: ({ formData }: IChangeEvent, id: string | undefined) => void;
}) {
  if (typeof uiSchema === 'undefined') {
    uiSchema = {};
  }
  if (schema.uiSchema) {
    uiSchema = { ...uiSchema, ...schema.uiSchema };
  }

  // @ts-expect-error:next-line
  uiSchema.func_name = { 'ui:widget': 'hidden' };
  Object.entries(schema.properties).forEach(([prop, attrs]) => {
    // @ts-expect-error:next-line
    if (attrs.is_reporter) {
      // @ts-expect-error:next-line
      uiSchema[prop] = { 'ui:widget': 'hidden' };
    }
  });

  return (
    <>
      <Form
        schema={schema}
        uiSchema={uiSchema}
        validator={validator}
        onSubmit={typeof onSubmit !== 'undefined' ? onSubmit : log('submitted')}
        onError={typeof onError !== 'undefined' ? onError : log('errors')}
        fields={{ SchemaField: CustomSchemaField, ...(fields ? fields : {}) }}
        widgets={widgets}
        onChange={onChange}
      />
    </>
  );
}

export default FunctionForm;
