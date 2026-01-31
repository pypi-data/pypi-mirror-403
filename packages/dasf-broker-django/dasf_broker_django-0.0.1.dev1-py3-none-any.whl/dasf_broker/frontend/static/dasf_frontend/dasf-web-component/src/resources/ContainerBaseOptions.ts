// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import { DASFProgressReport } from '@dasf/dasf-messaging';

import { ConnectionOptions } from './connection';

import { RegistryFieldsType, RegistryWidgetsType } from '@rjsf/utils';

/** Valid layout options for a container. */
export enum LayoutOption {
  Rows = 'rows',
  Columns = 'columns',
}

/** Base options for creating a container for a DASF module, class or function
 *
 * This interface holds the options for handling responses, errors and progress
 * reports of the DASF backend module and serves as a basis for the
 * :class:`FunctionContainerOptions`, :class:`ClassContainerOptions` and
 * :class:`ModuleContainerOptions`.
 *
 * See also :class:`ConnectionOptions` for further options.
 */
export interface ContainerBaseOptions extends ConnectionOptions {
  /** Response handler for requests from the backend module.
   *
   * This argument can be used to overwrite the default response handler (which
   * is a plain JSON-dump of the response of the backend module). It must take
   * the response from the function in the backend module.
   */
  onResponse?: (responseData: unknown) => void;

  /** Prevent the default handling of responses
   *
   * This option can be used to prevent the default response handler in favor
   * of the given `onResponse` handler (in case
   * :attr:`skipDefaultResponseHandlerCheck` is ``undefined``). Setting this to
   * ``true`` means that the default response handler should be skipped.
   */
  skipDefaultResponseHandler: boolean;

  /** Handler to check if the default handling of responses should be skipped
   *
   * This option can be used to prevent the default response handler in favor
   * of the given `onResponse` handler. This argument takes a callable that
   * takes the response as an argument and returns a boolean
   * that specifies whether the default response handler should be used or not.
   * If omitted, the :attr:`skipDefaultResponseHandler` determines the behaviour.
   */
  skipDefaultResponseHandlerCheck?: (responseData: unknown) => boolean;

  /** Error handler for requests from the backend module.
   *
   * This argument can be used to overwrite the default error handler (which
   * is simple call to ``console.error``). It must take the error from the
   * function in the backend module.
   */
  onError?: (error: Error) => void;

  /** Prevent the default handling of errors
   *
   * This option can be used to prevent the default error handler in favor
   * of the given `onError` handler (in case
   * :attr:`skipDefaultErrorHandlerCheck` is ``undefined``). Setting this to
   * ``true`` means that the default error handler should be skipped.
   */
  skipDefaultErrorHandler: boolean;

  /** Handler to check if the the default handling of errors should be skipped
   *
   * This option can be used to prevent the default error handler in favor
   * of the given `onError` handler. This argument takes a callable that takes
   * the error as an argument and returns a boolean that specifies whether the
   * default error handler should be used or not. If omitted, the
   * :attr:`skipDefaultErrorHandler` determines the behaviour.
   */
  skipDefaultErrorHandlerCheck?: (error: Error) => boolean;

  /** Progress handler for progress reports from the backend module.
   *
   * This argument can be used to overwrite the default progress handler (which
   * is simple dump of the progress report). It must take an object holding the
   * :class:`dasf-messaging-typescript:DASFProgressReport` as `message` and the
   * report properties as `props`.
   */
  onProgress?: (value: { message: DASFProgressReport; props?: object }) => void;

  /** Prevent the default handling of progress reports
   *
   * This option can be used to prevent the default progress report handler in
   * favor of the given `onProgress` handler (in case
   * :attr:`skipDefaultProgressHandlerCheck` is ``undefined``). Setting this to
   * ``true`` means that the default progress report handler should be skipped.
   */
  skipDefaultProgressHandler?: boolean;

  /** Handler to check if the default progress report handler should be skipped
   *
   * This option can be used to prevent the default progress report handler in
   * favor of the given `onProgress` handler. It should be a callable that
   * takes the ``message`` and ``props`` as an argument and
   * returns a boolean that specifies whether the default progress report
   * handler should be used or not. If omitted, the
   * :attr:`skipDefaultProgressHandler` determines the behaviour.
   */
  skipDefaultProgressHandlerCheck?: (value: {
    message: DASFProgressReport;
    props?: object;
  }) => boolean;

  /** Dictionary of registered fields in the form.
   *
   * See `Custom Widgets and Fields in the RJSF docs <https://rjsf-team.github.io/react-jsonschema-form/docs/advanced-customization/custom-widgets-fields>`__
   * for more information.
   *
   */
  fields?: RegistryFieldsType;

  /** Dictionary of registered widgets in the form.
   *
   * See `Custom Widgets and Fields in the RJSF docs <https://rjsf-team.github.io/react-jsonschema-form/docs/advanced-customization/custom-widgets-fields>`__
   * for more information.
   */
  widgets?: RegistryWidgetsType;

  /** Option to check if html output from the backend module should be rendered
   *
   * This option can be used to check, if strings returned by the DASF backend
   * module should be interpreted as HTML, or not. Note that option can be
   * dangerous if you cannot trust the backend module entirely!
   */
  renderStringAsHtml?: boolean;

  /** Layout option for the container
   *
   * Can be ``'rows'`` such that the content is organized in rows, or
   * ``'columns'`` such that the content is organized in 2 columns (on
   * large screens).
   */
  layout?: LayoutOption;
}
