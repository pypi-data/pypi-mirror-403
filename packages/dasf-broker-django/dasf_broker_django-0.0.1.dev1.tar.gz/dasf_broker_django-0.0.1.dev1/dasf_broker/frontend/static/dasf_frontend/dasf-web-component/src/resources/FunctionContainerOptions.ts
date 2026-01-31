// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import { RJSFSchema, UiSchema } from '@rjsf/utils';

import { ContainerBaseOptions } from './ContainerBaseOptions';

/** Options for the :func:`FunctionContainer <FunctionContainer.default>` component
 *
 * See also :class:`ContainerBaseOptions` for further options.
 * */
export interface FunctionContainerOptions extends ContainerBaseOptions {
  /** The id of a ``<script>`` element with JSON-encoded JSONSchema that is
   * used to render the function form.
   *
   * Pass this argument when you want to read the JSONSchema from the HTML
   * document, rather then the `schema` argument or by connecting to the
   * backend module.
   *
   * .. dropdown:: Example
   *
   *     The following JSON schema can be used by passing
   *     ``schemaElement="function-schema"``:
   *
   *     .. code-block:: html
   *
   *         <script id="function-schema" type="application/json">
   *           {
   *             "description": "Get the version of the backend module.",
   *             "properties": {
   *               "func_name": {
   *                 "const": "version_info",
   *                 "description": "The name of the function. Must be 'version_info'",
   *                 "title": "Func Name"
   *               }
   *             },
   *             "required": [
   *               "func_name"
   *             ],
   *             "title": "FuncVersionInfo",
   *             "type": "object"
   *           }
   *         </script>
   */
  schemaElement?: string;

  /** The schema to use for the function form
   *
   * Pass this argument when you want to prevent getting the JSONSchema from
   * the backend module. Note that this argument is superseeded by
   * `schemaElement`.
   */
  schema?: RJSFSchema;

  /** JSONSchema for rendering the user interface
   *
   * see https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema
   * for details
   */
  uiSchema?: UiSchema;

  /** Description of the function output
   *
   * This optional argument can be used, to label the output. Note that this
   * does not have an effect if the `onResponse` handler handles the request.
   */
  outputDescription?: string;

  /** The name of the function to render
   *
   * This option can be used if no `schemaElement` or `schema` is passed to the
   * constructor. In this case, the JSONschema is loaded from the backend module.
   * If `functionName` is undefined, we will render the first function in the
   * list.
   */
  functionName?: string;

  /** Constructor data for the backend class
   *
   * If this function is not an independent function but rather a method of
   * a class in the backend module, you have to pass the data for the
   * constructor as `constructorData`. See also :class:`ClassContainer`.
   */
  constructorData?: object;
}
