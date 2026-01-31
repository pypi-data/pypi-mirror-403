// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

import { DASFConnection } from '@dasf/dasf-messaging';
import { WebsocketUrlBuilder } from '@dasf/dasf-messaging';

/** Options to create a websocket connection to a DASF backend module
 *
 * This interface holds the options for the :func:`getConnection` function
 * to create a new :class:`dasf-messaging-typescript:DASFConnection`.
 */
export interface ConnectionOptions {
  /** A `DASFConnection` to a backend module or a callable that creates one.
   *
   * Provide a :class:`dasf-messaging-typescript:DASFConnection` to a DASF
   * backend module, or a function that creates one. If not provided, we will
   * create one from the given `websocketUrl` and `topic`.
   */
  connection?: DASFConnection | (() => DASFConnection);

  /** The websocket url to a DASF backend module
   *
   * If no `connection` is provided, this will be used to create a connection
   * to a DASF backend module. `topic` is required as well, see
   * :class:`dasf-messaging-typescript:WebsocketUrlBuilder`.
   */
  websocketUrl?: string;

  /** The topic for a DASF backend module
   *
   * If no `connection` is provided, this will be used to create a connection
   * to a DASF backend module. `websocketUrl` is required as well, see
   * :class:`dasf-messaging-typescript:WebsocketUrlBuilder`.
   */
  topic?: string;
}

/** Create a websocket connection to a DASF backend module
 *
 * This function creates a new :class:`dasf-messaging-typescript:DASFConnection`
 * to a backend module. When a :attr:`connection <ConnectionOptions.connection?>`
 * is provided, :attr:`websocketUrl <ConnectionOptions.websocketUrl?>` and
 * :attr:`topic <ConnectionOptions.topic?>` are ignored.
 *
 * @param options - The :class:`ConnectionOptions` to get the connection.
 */
export function getConnection({
  connection,
  websocketUrl,
  topic,
}: ConnectionOptions): DASFConnection {
  if (typeof connection === 'undefined') {
    return new DASFConnection(
      // @ts-expect-error:next-line
      new WebsocketUrlBuilder(websocketUrl, topic),
    );
  } else if (typeof connection === 'function') {
    return connection();
  } else {
    return connection;
  }
}
