import { BrowserRouter, Route, Routes } from 'react-router';
import { Layout } from './components/Layout';
import { AppConfigProvider } from './config';
import { HomePage } from './pages/HomePage';
import { NotFoundPage } from './pages/NotFoundPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <AppConfigProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AppConfigProvider>
  );
}
