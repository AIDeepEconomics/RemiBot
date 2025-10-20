import { Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { ConfiguracionView } from "./views/ConfiguracionView";
import { DocumentacionView } from "./views/DocumentacionView";
import { InicioView } from "./views/InicioView";
import { LogsView } from "./views/LogsView";
import { RemitosView } from "./views/RemitosView";

export default function App(): JSX.Element {
  return (
    <AppLayout>
      <Suspense fallback={<div>Cargando...</div>}>
        <Routes>
          <Route path="/" element={<InicioView />} />
          <Route path="/remitos" element={<RemitosView />} />
          <Route path="/configuracion" element={<ConfiguracionView />} />
          <Route path="/documentacion" element={<DocumentacionView />} />
          <Route path="/logs" element={<LogsView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </AppLayout>
  );
}
