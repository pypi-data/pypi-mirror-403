import r2wc from '@r2wc/react-to-web-component';
// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import FunctionContainer from './components/FunctionContainer.tsx';
import ClassContainer from './components/ClassContainer.tsx';
import ModuleContainer from './components/ModuleContainer.tsx';

const WebFunctionContainer = r2wc(FunctionContainer, {
  props: {
    schemaElement: 'string',
    schema: 'json',
    uiSchema: 'json',
    connection: 'function',
    websocketUrl: 'string',
    topic: 'string',
    outputDescription: 'string',
    functionName: 'string',
    skipDefaultResponseHandler: 'boolean',
    skipDefaultResponseHandlerCheck: 'function',
    skipDefaultErrorHandler: 'boolean',
    skipDefaultErrorHandlerCheck: 'function',
    skipDefaultProgressHandler: 'boolean',
    skipDefaultProgressHandlerCheck: 'function',
    constructorData: 'json',
    renderStringAsHtml: 'boolean',
    layout: 'string',
  },
  events: {
    onResponse: {},
    onError: {},
    onProgress: {},
  },
});

const WebClassContainer = r2wc(ClassContainer, {
  props: {
    apiInfoElement: 'string',
    apiInfo: 'json',
    uiSchema: 'json',
    connection: 'function',
    websocketUrl: 'string',
    topic: 'string',
    className: 'string',
    skipDefaultResponseHandler: 'boolean',
    skipDefaultResponseHandlerCheck: 'function',
    skipDefaultErrorHandler: 'boolean',
    skipDefaultErrorHandlerCheck: 'function',
    skipDefaultProgressHandler: 'boolean',
    skipDefaultProgressHandlerCheck: 'function',
    renderStringAsHtml: 'boolean',
    layout: 'string',
  },
  events: {
    onResponse: {},
    onError: {},
    onProgress: {},
  },
});

const WebModuleContainer = r2wc(ModuleContainer, {
  props: {
    apiInfoElement: 'string',
    apiInfo: 'json',
    member: 'string',
    connection: 'function',
    websocketUrl: 'string',
    topic: 'string',
    skipDefaultResponseHandler: 'boolean',
    skipDefaultResponseHandlerCheck: 'function',
    skipDefaultErrorHandler: 'boolean',
    skipDefaultErrorHandlerCheck: 'function',
    skipDefaultProgressHandler: 'boolean',
    skipDefaultProgressHandlerCheck: 'function',
    renderStringAsHtml: 'boolean',
    layout: 'string',
    updateUrl: 'boolean',
  },
  events: {
    onResponse: {},
    onError: {},
    onProgress: {},
  },
});

customElements.define('dasf-function', WebFunctionContainer);
customElements.define('dasf-class', WebClassContainer);
customElements.define('dasf-module', WebModuleContainer);
