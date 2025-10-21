import { useMemo } from "react";

interface Remito {
  id_remito: string;
  nombre_chacra: string;
  nombre_destino: string;
  peso_estimado_tn: number;
  estado_remito: string;
  activo: boolean;
}

const mockRemitos: Remito[] = [];

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
