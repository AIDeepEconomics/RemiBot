const exampleLogs = [
  {
    id: "1",
    timestamp: new Date().toISOString(),
    tipo: "INFO",
    detalle: "Inicio de la aplicación frontend"
  }
];

export function LogsView(): JSX.Element {
  return (
    <section>
      <header>
        <h1>Logs</h1>
        <p>Monitorea eventos relevantes registrados por el sistema.</p>
      </header>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Hora</th>
              <th>Tipo</th>
              <th>Detalle</th>
            </tr>
          </thead>
          <tbody>
            {exampleLogs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
                <td>
                  <span className={`badge badge-${log.tipo.toLowerCase()}`}>{log.tipo}</span>
                </td>
                <td>{log.detalle}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
