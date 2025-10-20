export function DocumentacionView(): JSX.Element {
  return (
    <section>
      <header>
        <h1>Documentación de la API</h1>
        <p>
          Accede a la documentación generada automáticamente por el backend (FastAPI).
          Cuando el backend esté desplegado, podrás cargar el OpenAPI aquí.
        </p>
      </header>
      <article className="card">
        <h2>OpenAPI</h2>
        <p>
          Próximamente se integrará un visor embebido de la documentación (`/docs`). Por ahora
          puedes consultar directamente la URL del backend.
        </p>
        <code>https://backend.remibot.example/docs</code>
      </article>
    </section>
  );
}
