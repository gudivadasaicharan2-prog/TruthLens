/**
 * Tests for Detect (Upload) page component.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Detect from '../src/pages/Detect';

// Mock the API
jest.mock('../src/services/api', () => ({
  analyzeImage: jest.fn(() => Promise.resolve({
    verdict: 'Real',
    confidence: 0.95,
    ai_probability: 5,
  })),
}));

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Detect Page', () => {
  test('renders upload area', () => {
    renderWithRouter(<Detect />);
    expect(screen.getByText(/upload/i)).toBeInTheDocument();
  });

  test('displays file input', () => {
    renderWithRouter(<Detect />);
    const fileInput = screen.getByRole('button', { hidden: true });
    expect(fileInput).toBeInTheDocument();
  });

  test('shows drag and drop text', () => {
    renderWithRouter(<Detect />);
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
  });

  test('displays supported formats', () => {
    renderWithRouter(<Detect />);
    expect(screen.getByText(/jpeg|png|webp/i)).toBeInTheDocument();
  });
});
