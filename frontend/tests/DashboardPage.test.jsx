/**
 * Tests for Dashboard page component.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../src/pages/Dashboard';

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Dashboard Page', () => {
  test('renders dashboard heading', () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });

  test('displays analysis history section', () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByText(/history|recent/i)).toBeInTheDocument();
  });
});
