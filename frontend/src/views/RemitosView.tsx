import { useMemo } from "react";

const mockRemitos = [];

export function RemitosView(): JSX.Element {
  const remitos = useMemo(() => mockRemitos, []);

  return (
    <section>
      <header>
        <h1>Remitos</h1>
        <p>Consulta y gestiona los remitos generados por el chatbot.</p>
      </header>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>ID Remito</th>
              <th>Chacra</th>
              <th>Destino</th>
              <th>Peso (t)</th>
              <th>Estado</th>
              <th>Activo</th>
            </tr>
          </thead>
          <tbody>
            {remitos.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty">
                  Aún no hay remitos registrados.
                </td>
              </tr>
            ) : (
              remitos.map((remito) => (
                <tr key={remito.id_remito}>
                  <td>{remito.id_remito}</td>
                  <td>{remito.nombre_chacra}</td>
                  <td>{remito.nombre_destino}</td>
                  <td>{remito.peso_estimado_tn}</td>
                  <td>{remito.estado_remito}</td>
                  <td>{remito.activo ? "Sí" : "No"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
