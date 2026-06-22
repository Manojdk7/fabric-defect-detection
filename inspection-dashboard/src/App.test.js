import { render, screen } from '@testing-library/react';
import App from './App';

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          status: 'healthy',
          service: 'Quality Inspection System',
          version: '1.0.0',
        }),
    }),
  );
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('renders inspection dashboard', async () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: /quality inspection system/i })).toBeInTheDocument();
  expect(await screen.findByText(/healthy - quality inspection system/i)).toBeInTheDocument();
});
