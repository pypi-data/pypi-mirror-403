// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import FunctionContainer from './FunctionContainer';
import ClassContainer from './ClassContainer';
import { getConnection } from '../resources/connection';
import {
  DASFConnection,
  FunctionApiInfo,
  ClassApiInfo,
  ModuleApiInfo,
} from '@dasf/dasf-messaging';

import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import KeyboardDoubleArrowLeftIcon from '@mui/icons-material/KeyboardDoubleArrowLeft';

// @ts-expect-error: importing React is necessary for react@18.2.0
import React, { useEffect } from 'react';
import { useState } from 'react';

import { ModuleContainerOptions } from '../resources/ModuleContainerOptions';
import { LayoutOption } from '../resources/ContainerBaseOptions';
import usePrevious from '../resources/usePrevious';

/** A container to render a form for an entire DASF backend module
 *
 * This react component can be used to render an entire DASF backend module and
 * its classes and functions. You can either provide the
 * :attr:`connection <ConnectionOptions.connection?>`, or the details
 * (:attr:`websocketUrl <ConnectionOptions.websocketUrl?>` and
 * :attr:`topic <ConnectionOptions.topic?>`) how to create one. And you can
 * either provide the api info for the module directly (via
 * :attr:`schema <ModuleContainerOptions.apiInfo?>`), or pass the id of
 * an HTML `script` element that holds the info (via
 * :attr:`schemaElement <ModuleContainerOptions.apiInfoElement?>`).
 * If none of this is specified, we will get the api info from the backend
 * module and render the form upon response.
 *
 * For more information on the available options, see
 * :class:`ModuleContainerOptions`.
 *
 * .. dropdown:: Example
 *
 *     .. code-block:: tsx
 *
 *         <ModuleContainer
 *           connection={connection}
 *           onResponse={(responseData) => {console.log(responseData)}}
 *         />
 *
 * @param options - Options for the component, see
 *   :class:`ModuleContainerOptions` for documentation
 */

function ModuleContainer({
  apiInfoElement,
  apiInfo,
  uiSchema,
  member,
  connection,
  websocketUrl,
  topic,
  layout = LayoutOption.Columns,
  updateUrl = false,
  ...props
}: ModuleContainerOptions) {
  const [selectedMember, setSelectedMember] = useState<string>(
    typeof member === 'undefined' ? '' : member,
  );
  const previousMember = usePrevious(selectedMember);

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
      ModuleApiInfo,
    );
  }
  const [finalApiInfo, setFinalApiInfo] = useState<ModuleApiInfo | undefined>(
    apiInfo,
  );
  if (typeof finalApiInfo === 'undefined') {
    dasfConnection.getApiInfo().then((apiInfo) => {
      setFinalApiInfo(apiInfo);
    });
  }
  useEffect(() => {
    if (
      updateUrl &&
      previousMember != selectedMember &&
      typeof previousMember != 'undefined'
    ) {
      const newUrl = new URL(
        (previousMember ? '../' : '') +
          selectedMember +
          (selectedMember ? '/' : ''),
        window.location.href,
      );
      history.replaceState(null, '', newUrl);
    }
  }, [selectedMember, previousMember, updateUrl]);

  return (
    <>
      {finalApiInfo && (
        <Collapse in={!selectedMember} timeout="auto" unmountOnExit>
          <Grid container spacing={{ xs: 2, md: 3 }}>
            {finalApiInfo.functions
              // @ts-expect-error:next-line
              .concat(finalApiInfo.classes)
              .map((functionInfo: FunctionApiInfo) => (
                <Grid
                  key={functionInfo.name}
                  size={{ xs: 12, md: layout == LayoutOption.Rows ? 12 : 6 }}
                >
                  <Card variant="outlined">
                    <CardActionArea
                      onClick={() => setSelectedMember(functionInfo.name)}
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
                        <Typography variant="h5" component="div" sx={{ mb: 2 }}>
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
              ))}
          </Grid>
        </Collapse>
      )}
      {finalApiInfo &&
        finalApiInfo.functions.map((functionInfo: FunctionApiInfo) => (
          <Collapse
            in={selectedMember == functionInfo.name}
            timeout="auto"
            key={functionInfo.name}
            unmountOnExit
          >
            <Button
              variant="text"
              onClick={() => setSelectedMember('')}
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
              layout={layout}
              {...props}
            />
          </Collapse>
        ))}
      {finalApiInfo &&
        finalApiInfo.classes.map((classInfo: ClassApiInfo) => (
          <Collapse
            in={classInfo.name == selectedMember}
            timeout="auto"
            key={classInfo.name}
            unmountOnExit
          >
            <Button
              variant="text"
              onClick={() => setSelectedMember('')}
              startIcon={<KeyboardDoubleArrowLeftIcon />}
            >
              All functions
            </Button>
            <ClassContainer
              key={classInfo.name}
              apiInfo={classInfo}
              uiSchema={uiSchema}
              connection={dasfConnection}
              layout={layout}
              {...props}
            />
          </Collapse>
        ))}
    </>
  );
}

export default ModuleContainer;
