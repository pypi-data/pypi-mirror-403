// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0
import { UiSchema } from '@rjsf/utils';
import { ClassApiInfo } from '@dasf/dasf-messaging';
import { ContainerBaseOptions } from './ContainerBaseOptions';

/** Options for the :func:`ClassContainer <ClassContainer.default>` component
 *
 * See also :class:`ContainerBaseOptions` for further options.
 */
export interface ClassContainerOptions extends ContainerBaseOptions {
  /** The id of a ``<script>`` element with JSON-encoded API Info that is
   * used to render the function forms.
   *
   * Pass this argument when you want to read the API info from the HTML
   * document, rather then the `schema` argument or by connecting to the
   * backend module. The content must be an encoded
   * :class:`dasf-messaging-typescript:ClassApiInfo`
   *
   * .. dropdown:: Example
   *
   *     The following JSON schema can be used by passing
   *     ``apiInfoElement="class-info"``:
   *
   *     .. code-block:: html
   *
   *         <script id="class-info" type="application/json">
   *           {
   *             "name": "SomeTestClass",
   *             "rpc_schema": {
   *               "description": "Some test class for DASF",
   *               "properties": {
   *                 "a": {
   *                   "description": "A number to work with",
   *                   "title": "A",
   *                   "type": "integer"
   *                 },
   *                 "class_name": {
   *                   "const": "SomeTestClass",
   *                   "description": "The name of the function. Must be 'SomeTestClass'",
   *                   "title": "Class Name"
   *                 }
   *               },
   *               "required": [
   *                 "a",
   *                 "class_name"
   *               ],
   *               "title": "ClassSomeTestClass",
   *               "type": "object"
   *             },
   *             "methods": [
   *               {
   *                 "name": "add",
   *                 "rpc_schema": {
   *                   "description": "Add another number to `a`",
   *                   "properties": {
   *                     "func_name": {
   *                       "const": "add",
   *                       "description": "The name of the function. Must be 'add'",
   *                       "title": "Func Name"
   *                     },
   *                     "b": {
   *                       "description": "The number to add to",
   *                       "title": "B",
   *                       "type": "integer"
   *                     }
   *                   },
   *                   "required": [
   *                     "func_name",
   *                     "b"
   *                   ],
   *                   "title": "MethClassSomeTestClassAdd",
   *                   "type": "object"
   *                 },
   *                 "return_schema": {
   *                   "default": null,
   *                   "description": "Sum of `a` and `b`",
   *                   "title": "MethClassSomeTestClassAdd",
   *                   "type": "integer"
   *                 }
   *               }
   *             ]
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
   * See also :class:`dasf-messaging-typescript:ClassApiInfo` and pythons
   * :external:py:meth:`demessaging.backend.class_.BackendClass.get_api_info`.
   */
  apiInfo?: ClassApiInfo;

  /** JSONSchema for rendering the user interface
   *
   * see https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema
   * for details
   */
  uiSchema?: UiSchema;

  /** The name of the class to render
   *
   * This option can be used if no `apiInfoElement` or `apiInfo` is passed to the
   * constructor. In this case, the api info is loaded from the backend module.
   * If `className` is undefined, we will render the first class in the
   * list.
   */
  className?: string;
}
