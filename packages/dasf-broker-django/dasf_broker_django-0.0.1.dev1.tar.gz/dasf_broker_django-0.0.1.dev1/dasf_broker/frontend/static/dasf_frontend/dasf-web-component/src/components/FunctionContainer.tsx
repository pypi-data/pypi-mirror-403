// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import FunctionForm from './FunctionForm';
import { IChangeEvent } from '@rjsf/core';
import OutputContainer from './OutputContainer';
import ProgressContainer from './ProgressContainer';
import { getConnection } from '../resources/connection';
import { FunctionContainerOptions } from '../resources/FunctionContainerOptions';
import { DASFConnection, DASFProgressReport } from '@dasf/dasf-messaging';

// @ts-expect-error: importing React is necessary for react@18.2.0
import React from 'react';
import { useState, FormEvent, useRef } from 'react';

import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Grid from '@mui/material/Grid2';

import { LayoutOption } from '../resources/ContainerBaseOptions';

/** A container to render a form for a function in a DASF backend module
 *
 * This react component can be used to render a single function of a DASF
 * backend module. You can either provide the
 * :attr:`connection <ConnectionOptions.connection?>`, or the details
 * (:attr:`websocketUrl <ConnectionOptions.websocketUrl?>` and
 * :attr:`topic <ConnectionOptions.topic?>`) how to create one. And you can
 * either provide the JSONschema for the function directly (via
 * :attr:`schema <FunctionContainerOptions.schema?>`), or pass the id of
 * an HTML `script` element that holds the schema (via
 * :attr:`schemaElement <FunctionContainerOptions.schemaElement?>`).
 * If none of this is specified, we will get the JSONschema from the backend
 * module and render the form upon response.
 *
 * For more information on the available options, see
 * :class:`FunctionContainerOptions`.
 *
 * .. dropdown:: Example
 *
 *     .. code-block:: tsx
 *
 *         <FunctionContainer
 *           connection={connection}
 *           functionName="test_function"
 *           onResponse={(responseData) => {console.log(responseData)}}
 *         />
 *
 * @param options - Options for the component, see
 *   :class:`FunctionContainerOptions` for documentation
 */
function FunctionContainer({
  schemaElement,
  schema,
  uiSchema,
  outputDescription,
  connection,
  websocketUrl,
  topic,
  functionName,
  onResponse,
  skipDefaultResponseHandler = false,
  skipDefaultResponseHandlerCheck,
  onError,
  skipDefaultErrorHandler = false,
  skipDefaultErrorHandlerCheck,
  onProgress,
  skipDefaultProgressHandler = false,
  skipDefaultProgressHandlerCheck,
  fields,
  widgets,
  constructorData,
  renderStringAsHtml = false,
  layout = LayoutOption.Columns,
}: FunctionContainerOptions) {
  if (typeof schemaElement != 'undefined') {
    schema = JSON.parse(
      // @ts-expect-error:next-line
      document.getElementById(schemaElement)?.textContent,
    );
  }
  const [output, setOutput] = useState<unknown>(null);
  const [progress, setProgress] = useState<DASFProgressReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [finalSchema, setFinalSchema] = useState(schema);
  const [outputDescriptionState, setOutputDescriptionState] = useState<
    string | undefined
  >(outputDescription);
  // @ts-expect-error:next-line
  const buttonRef: { current: HTMLButtonElement } = useRef(null);

  function checkskipDefaultOnResponse(responseData: unknown): boolean {
    if (typeof skipDefaultResponseHandlerCheck === 'undefined') {
      return skipDefaultResponseHandler;
    } else {
      return skipDefaultResponseHandlerCheck(responseData);
    }
  }

  function checkskipDefaultOnProgress(value: {
    message: DASFProgressReport;
    props?: object;
  }): boolean {
    if (typeof skipDefaultProgressHandlerCheck === 'undefined') {
      return skipDefaultProgressHandler;
    } else {
      return skipDefaultProgressHandlerCheck(value);
    }
  }

  function checkskipDefaultOnError(error: Error): boolean {
    if (typeof skipDefaultErrorHandlerCheck === 'undefined') {
      return skipDefaultErrorHandler;
    } else {
      return skipDefaultErrorHandlerCheck(error);
    }
  }

  const defaultOnReponse = (responseData: unknown) => {
    setOutput(responseData);
  };

  const defaultOnProgress = (value: {
    message: DASFProgressReport;
    props?: object;
  }) => {
    setProgress(value.message);
  };

  const handleProgress = (value: {
    message: DASFProgressReport;
    props?: object;
  }) => {
    if (typeof onProgress === 'undefined') {
      defaultOnProgress(value);
    } else {
      onProgress(value);
      if (!checkskipDefaultOnProgress(value)) {
        defaultOnProgress(value);
      }
    }
  };

  const handleResponse = (response: unknown) => {
    setLoading(false);
    buttonRef.current.disabled = false;
    buttonRef.current.classList.remove('Mui-disabled');

    if (typeof onResponse === 'undefined') {
      defaultOnReponse(response);
    } else {
      onResponse(response);
      if (!checkskipDefaultOnResponse(response)) {
        defaultOnReponse(response);
      }
    }
  };

  const handleError = (error: Error) => {
    setOutputDescriptionState('Request failed!');
    if (typeof onError === 'undefined') {
      console.error(error);
    } else {
      onError(error);
      if (!checkskipDefaultOnError(error)) {
        console.error('miao!', error);
      }
    }
  };

  const dasfConnection: DASFConnection = getConnection({
    connection,
    websocketUrl,
    topic,
  });
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const onSubmit = ({ formData }: IChangeEvent, _event: FormEvent) => {
    setLoading(true);
    setOutput(null);
    setOutputDescriptionState(outputDescription);
    buttonRef.current.disabled = true;
    buttonRef.current.classList.add('Mui-disabled');

    if (typeof constructorData != 'undefined') {
      formData = { ...constructorData, function: formData };
    }

    dasfConnection
      .sendRequest(formData, handleProgress)
      .then(handleResponse)
      .catch(handleError);
  };
  if (typeof uiSchema === 'undefined') {
    uiSchema = {};
  }
  uiSchema['ui:submitButtonOptions'] = {
    props: { ref: buttonRef }, // don't use the disabled property here because this would trigger a rerender on every submit
  };
  if (typeof finalSchema === 'undefined') {
    dasfConnection.getApiInfo().then((api_info) => {
      if (typeof functionName === 'undefined') {
        setFinalSchema(api_info.functions[0].rpcSchema);
      } else {
        setFinalSchema(
          api_info.functions.filter((f) => f.name == functionName)[0].rpcSchema,
        );
      }
    });
  }
  return (
    <>
      <Grid container spacing={2}>
        <Grid
          size={{
            xs: 12,
            md: layout == LayoutOption.Rows ? 12 : progress || output ? 6 : 12,
          }}
        >
          {finalSchema && (
            <FunctionForm
              schema={finalSchema}
              uiSchema={uiSchema}
              onSubmit={onSubmit}
              fields={fields}
              widgets={widgets}
            />
          )}
          {loading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
            </Box>
          )}
        </Grid>
        {(progress || output != null) && (
          <Grid size={{ xs: 12, md: layout == LayoutOption.Rows ? 12 : 6 }}>
            {progress && <ProgressContainer report={progress} />}
            {output != null && (
              <OutputContainer
                content={output}
                description={outputDescriptionState}
                renderStringAsHtml={renderStringAsHtml}
              />
            )}
          </Grid>
        )}
      </Grid>
    </>
  );
}

export default FunctionContainer;
