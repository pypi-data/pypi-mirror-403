// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import FunctionForm from './FunctionForm';
import FunctionContainer from './FunctionContainer';
import { IChangeEvent } from '@rjsf/core';
import { getConnection } from '../resources/connection';
import {
  ClassApiInfo,
  DASFConnection,
  FunctionApiInfo,
} from '@dasf/dasf-messaging';

// @ts-expect-error: importing React is necessary for react@18.2.0
import React from 'react';
import { useState } from 'react';

import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import KeyboardDoubleArrowLeftIcon from '@mui/icons-material/KeyboardDoubleArrowLeft';
import { ClassContainerOptions } from '../resources/ClassContainerOptions';

import { LayoutOption } from '../resources/ContainerBaseOptions';

/** A container to render a forms for a class in a DASF backend module
 *
 * This react component can be used to render a single class and its methods of
 * a DASF backend module. You can either provide the
 * :attr:`connection <ConnectionOptions.connection?>`, or the details
 * (:attr:`websocketUrl <ConnectionOptions.websocketUrl?>` and
 * :attr:`topic <ConnectionOptions.topic?>`) how to create one. And you can
 * either provide the api info for the class directly (via
 * :attr:`schema <ClassContainerOptions.apiInfo?>`), or pass the id of
 * an HTML `script` element that holds the info (via
 * :attr:`schemaElement <ClassContainerOptions.apiInfoElement?>`).
 * If none of this is specified, we will get the api info from the backend
 * module and render the form upon response.
 *
 * For more information on the available options, see
 * :class:`ClassContainerOptions`.
 *
 * .. dropdown:: Example
 *
 *     .. code-block:: tsx
 *
 *         <ClassContainer
 *           connection={connection}
 *           className="SomeClass"
 *           onResponse={(responseData) => {console.log(responseData)}}
 *         />
 *
 * @param options - Options for the component, see
 *   :class:`ClassContainerOptions` for documentation
 */
function ClassContainer({
  apiInfoElement,
  apiInfo,
  uiSchema,
  connection,
  websocketUrl,
  topic,
  className,
  fields,
  widgets,
  layout = LayoutOption.Columns,
  ...props
}: ClassContainerOptions) {
  const [selectedCard, setSelectedCard] = useState<number>(-1);
  const [constructorData, setConstructorData] = useState({});

  const dasfConnection: DASFConnection = getConnection({
    connection,
    websocketUrl,
    topic,
  });

  if (typeof apiInfoElement != 'undefined') {
    apiInfo = dasfConnection.jsonCoder.deserializeObject(
      JSON.parse(
        // @ts-expect-error:next-line
        document.getElementById(apiInfoElement)?.textContent,
      ),
      ClassApiInfo,
    );
  }
  const [finalApiInfo, setFinalApiInfo] = useState<ClassApiInfo | undefined>(
    apiInfo,
  );

  if (typeof uiSchema === 'undefined') {
    uiSchema = {};
  }

  const constructorUiSchema = {
    ...uiSchema,
    ...{
      'ui:submitButtonOptions': { norender: true },
      class_name: { 'ui:widget': 'hidden' },
    },
  };
  if (typeof finalApiInfo === 'undefined') {
    dasfConnection.getApiInfo().then((api_info) => {
      if (typeof className === 'undefined') {
        setFinalApiInfo(api_info.classes[0]);
      } else {
        setFinalApiInfo(api_info.classes.filter((c) => c.name == className)[0]);
      }
    });
  }
  const onChange = ({ formData }: IChangeEvent) => {
    setConstructorData(formData);
  };
  return (
    <>
      {finalApiInfo && (
        <>
          <FunctionForm
            schema={finalApiInfo.rpcSchema}
            uiSchema={constructorUiSchema}
            onChange={onChange}
            fields={fields}
            widgets={widgets}
          ></FunctionForm>
          <Collapse in={selectedCard == -1} timeout="auto" unmountOnExit>
            <Grid container spacing={{ xs: 2, md: 3 }}>
              {finalApiInfo.methods.map(
                (functionInfo: FunctionApiInfo, index: number) => (
                  <Grid
                    key={functionInfo.name}
                    size={{ xs: 12, md: layout == LayoutOption.Rows ? 12 : 6 }}
                  >
                    <Card variant="outlined">
                      <CardActionArea
                        onClick={() => setSelectedCard(index)}
                        data-active={undefined}
                        sx={{
                          height: '100%',
                          '&[data-active]': {
                            backgroundColor: 'action.selected',
                            '&:hover': {
                              backgroundColor: 'action.selectedHover',
                            },
                          },
                        }}
                      >
                        <CardContent>
                          <Typography
                            variant="h5"
                            component="div"
                            sx={{ mb: 2 }}
                          >
                            {functionInfo.name}
                          </Typography>
                          {functionInfo.rpcSchema.description && (
                            <Typography
                              variant="body2"
                              sx={{ color: 'text.secondary' }}
                            >
                              {functionInfo.rpcSchema.description}
                            </Typography>
                          )}
                        </CardContent>
                      </CardActionArea>
                    </Card>
                  </Grid>
                ),
              )}
            </Grid>
          </Collapse>
          {finalApiInfo.methods.map(
            (functionInfo: FunctionApiInfo, index: number) => (
              <Collapse
                in={index == selectedCard}
                timeout="auto"
                key={functionInfo.name}
                unmountOnExit
              >
                <Button
                  variant="text"
                  onClick={() => setSelectedCard(-1)}
                  startIcon={<KeyboardDoubleArrowLeftIcon />}
                >
                  All functions
                </Button>
                <FunctionContainer
                  key={functionInfo.name}
                  schema={functionInfo.rpcSchema}
                  uiSchema={uiSchema}
                  outputDescription={functionInfo.returnSchema.description}
                  connection={dasfConnection}
                  constructorData={constructorData}
                  fields={fields}
                  widgets={widgets}
                  layout={layout}
                  {...props}
                />
              </Collapse>
            ),
          )}
        </>
      )}
    </>
  );
}

export default ClassContainer;
