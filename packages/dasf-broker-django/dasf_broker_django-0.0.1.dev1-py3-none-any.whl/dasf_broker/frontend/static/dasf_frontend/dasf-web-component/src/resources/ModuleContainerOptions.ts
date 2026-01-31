// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import { UiSchema } from '@rjsf/utils';
import { ModuleApiInfo } from '@dasf/dasf-messaging';

import { ContainerBaseOptions } from './ContainerBaseOptions';

/** Options for the :func:`ModuleContainer <ModuleContainer.default>` component
 *
 * See also :class:`ContainerBaseOptions` for further options.
 * */
export interface ModuleContainerOptions extends ContainerBaseOptions {
  /** The id of a ``<script>`` element with JSON-encoded API Info that is
   * used to render the function forms.
   *
   * Pass this argument when you want to read the API info from the HTML
   * document, rather then the `schema` argument or by connecting to the
   * backend module. The content must be an encoded
   * :class:`dasf-messaging-typescript:ModuleApiInfo`
   *
   * .. dropdown:: Example
   *
   *     The following JSON schema can be used by passing
   *     ``apiInfoElement="module-info"``:
   *
   *     .. code-block:: html
   *
   *         <script id="module-info" type="application/json">
   *           {
   *             "classes": [],
   *             "functions": [
   *               {
   *                 "name": "version_info",
   *                 "rpc_schema": {
   *                   "description": "Get the version of the test module.",
   *                   "properties": {
   *                     "func_name": {
   *                       "const": "version_info",
   *                       "description": "The name of the function. Must be 'version_info'",
   *                       "title": "Func Name",
   *                       "type": "string"
   *                     }
   *                   },
   *                   "required": [
   *                     "func_name"
   *                   ],
   *                   "title": "FuncVersionInfo",
   *                   "type": "object"
   *                 },
   *                 "return_schema": {
   *                   "additionalProperties": {
   *                     "type": "string"
   *                   },
   *                   "default": null,
   *                   "title": "FuncVersionInfo",
   *                   "type": "object"
   *                 }
   *               }
   *             ],
   *             "rpc_schema": {
   *               "$defs": {
   *                 "FuncVersionInfo": {
   *                   "description": "Get the version of extpar and extpar_client.",
   *                   "properties": {
   *                     "func_name": {
   *                       "const": "version_info",
   *                       "description": "The name of the function. Must be 'version_info'",
   *                       "title": "Func Name",
   *                       "type": "string"
   *                     }
   *                   },
   *                   "required": [
   *                     "func_name"
   *                   ],
   *                   "title": "FuncVersionInfo",
   *                   "type": "object"
   *                 }
   *               },
   *               "$ref": "#/$defs/FuncVersionInfo",
   *               "description": "Backend module for test-backend.",
   *               "title": "mytesttopic"
   *             }
   *           }
   *         </script>
   */
  apiInfoElement?: string;

  /** The api to use to render the forms
   *
   * Pass this argument when you want to prevent getting the api info from
   * the backend module. Note that this argument is superseeded by
   * `apiInfoElement`.
   *
   * See also :class:`dasf-messaging-typescript:ModuleApiInfo` and pythons
   * :external:py:meth:`demessaging.backend.module.BackendModule.get_api_info`.
   */
  apiInfo?: ModuleApiInfo;

  /** JSONSchema for rendering the user interface
   *
   * see https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema
   * for details
   */
  uiSchema?: UiSchema;

  /** The member in the DASF backend module to display
   *
   * If this is set, we will display the given member on start. If this is not
   * specified, we will render an overview.
   */
  member?: string;

  /** Update the URL when a function or class is expanded
   *
   * This boolean triggers an update of the window history when a function
   * or class is expanded. The name of the class/function is added to the
   * URL in the browser. This is especially useful when you want to use this
   * component in somewhat like a single-page web application without the
   * necessity to create your own router.
   */
  updateUrl?: boolean;
}
