// SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
//
// SPDX-License-Identifier: Apache-2.0

// @ts-expect-error: importing React is necessary for react@18.2.0
import React from 'react';
import { ReactElement } from 'react';
import ReactJsonView from '@microlink/react-json-view';

function OutputContainer({
  content,
  description,
  renderStringAsHtml = false,
}: {
  content: unknown;
  description?: string | ReactElement;
  renderStringAsHtml?: boolean;
}) {
  const handledTypes = renderStringAsHtml ? ['string', 'object'] : ['object'];

  const isUrl: (content: unknown) => boolean = (content) => {
    if (
      typeof content === 'string' &&
      (content.startsWith('http://') || content.startsWith('https://')) &&
      URL.canParse(content) &&
      !/\s/g.test(content)
    ) {
      return true;
    }
    return false;
  };
  return (
    <>
      {typeof content == 'string' && renderStringAsHtml && (
        <div dangerouslySetInnerHTML={{ __html: content }} />
      )}
      {typeof content == 'object' && content != null && (
        <ReactJsonView src={content} />
      )}
      {content != null && !handledTypes.includes(typeof content) && (
        <>
          <div>{description ? description : 'Output'}</div>

          {(isUrl(content) && (
            <a href={content as string} target="_blank">
              {content as string}
            </a>
          )) || <pre>{JSON.stringify(content, null, '    ')}</pre>}
        </>
      )}
    </>
  );
}

export default OutputContainer;
