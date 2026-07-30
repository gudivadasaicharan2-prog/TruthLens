/**
 * Tests for Settings page component.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Settings from '../src/pages/Settings';

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Settings Page', () => {
  test('renders settings heading', () => {
    renderWithRouter(<Settings />);
    expect(screen.getByText(/settings/i)).toBeInTheDocument();
  });

  test('displays account section', () => {
    renderWithRouter(<Settings />);
    expect(screen.getByText(/account|profile/i)).toBeInTheDocument();
  });
});
