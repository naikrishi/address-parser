import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components";
import { DetailPage, LoginPage, PipelinePage } from "./pages";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={(
          <ProtectedRoute>
            <PipelinePage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/parse/:parseId"
        element={(
          <ProtectedRoute>
            <DetailPage />
          </ProtectedRoute>
        )}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
