/**
 * Tests for Login page component.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../src/pages/Login';

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Login Page', () => {
  test('renders login form', () => {
    renderWithRouter(<Login />);
    expect(screen.getByText(/login/i)).toBeInTheDocument();
  });

  test('displays email input', () => {
    renderWithRouter(<Login />);
    const emailInput = screen.getByLabelText(/email/i) || screen.getByPlaceholderText(/email/i);
    expect(emailInput).toBeInTheDocument();
  });

  test('displays password input', () => {
    renderWithRouter(<Login />);
    const passwordInput = screen.getByLabelText(/password/i) || screen.getByPlaceholderText(/password/i);
    expect(passwordInput).toBeInTheDocument();
  });

  test('displays login button', () => {
    renderWithRouter(<Login />);
    const loginButton = screen.getByRole('button', { name: /login|sign in/i });
    expect(loginButton).toBeInTheDocument();
  });

  test('displays Google login option', () => {
    renderWithRouter(<Login />);
    expect(screen.getByText(/google/i)).toBeInTheDocument();
  });
});
