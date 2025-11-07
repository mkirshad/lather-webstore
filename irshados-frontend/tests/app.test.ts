import test from 'node:test'
import assert from 'node:assert/strict'
import { renderToString } from 'react-dom/server'
import React from 'react'

import App from '../src/App'

test('App renders without crashing', () => {
  const markup = renderToString(React.createElement(App))
  assert.ok(markup.length > 0, 'expected markup to be generated')
})
