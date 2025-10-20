export function InicioView(): JSX.Element {
  return (
    <section>
      <header>
        <h1>Resumen general</h1>
        <p>
          Bienvenido al panel de control de <strong>RemiBOT</strong>. Aquí podrás monitorear el estado
          de los remitos generados por el chatbot y revisar configuraciones clave.
        </p>
      </header>
      <div className="grid">
        <article className="card">
          <h2>Remitos activos</h2>
          <p className="metric">0</p>
          <p className="hint">Aún no hay remitos registrados.</p>
        </article>
        <article className="card">
          <h2>Peso total despachado</h2>
          <p className="metric">0 t</p>
          <p className="hint">El peso total irá apareciendo a medida que se creen remitos.</p>
        </article>
        <article className="card">
          <h2>Destinos recurrentes</h2>
          <p className="metric">-</p>
          <p className="hint">Próximamente se mostrarán estadísticas de destinos.</p>
        </article>
      </div>
    </section>
  );
}
