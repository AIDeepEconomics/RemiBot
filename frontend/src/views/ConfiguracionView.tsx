import { FormEvent, useEffect, useState } from "react";

interface ConfiguracionFormState {
  whatsapp_api_key: string;
  gpt_api_key: string;
  claude_api_key: string;
  llm_prompt: string;
  auth_password: string;
}

const initialState: ConfiguracionFormState = {
  whatsapp_api_key: "",
  gpt_api_key: "",
  claude_api_key: "",
  llm_prompt: "",
  auth_password: ""
};

export function ConfiguracionView(): JSX.Element {
  const [state, setState] = useState(initialState);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Cargar configuración al montar el componente
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await fetch("http://localhost:8000/config");
        if (response.ok) {
          const config = await response.json();
          setState({
            whatsapp_api_key: config.whatsapp_api_key || "",
            gpt_api_key: config.gpt_api_key || "",
            claude_api_key: config.claude_api_key || "",
            llm_prompt: config.llm_prompt || "",
            auth_password: ""
          });
        }
      } catch (error) {
        console.error("Error cargando configuración:", error);
        setStatus("Error al cargar la configuración");
      } finally {
        setLoading(false);
      }
    };
    loadConfig();
  }, []);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setState((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus("Guardando...");
    
    try {
      const response = await fetch("http://localhost:8000/config", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(state),
      });

      if (response.ok) {
        setStatus("✅ Configuración guardada exitosamente");
        setTimeout(() => setStatus(null), 3000);
      } else {
        const error = await response.json();
        setStatus(`❌ Error: ${error.detail || "Error al guardar"}`);
      }
    } catch (error) {
      console.error("Error guardando configuración:", error);
      setStatus("❌ Error de conexión al guardar");
    }
  };

  if (loading) {
    return (
      <section>
        <header>
          <h1>Configuración</h1>
          <p>Cargando configuración...</p>
        </header>
      </section>
    );
  }

  return (
    <section>
      <header>
        <h1>Configuración</h1>
        <p>Administra las credenciales y el prompt del bot.</p>
      </header>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          WhatsApp API Key
          <input
            type="password"
            name="whatsapp_api_key"
            value={state.whatsapp_api_key}
            onChange={handleChange}
            placeholder="Meta Cloud API token"
          />
        </label>
        <label>
          GPT API Key
          <input
            type="password"
            name="gpt_api_key"
            value={state.gpt_api_key}
            onChange={handleChange}
            placeholder="OpenAI API key"
          />
        </label>
        <label>
          Claude API Key
          <input
            type="password"
            name="claude_api_key"
            value={state.claude_api_key}
            onChange={handleChange}
            placeholder="Anthropic API key"
          />
        </label>
        <label>
          Prompt del LLM
          <textarea
            name="llm_prompt"
            value={state.llm_prompt}
            onChange={handleChange}
            rows={6}
            placeholder="Define las instrucciones base para el chatbot"
          />
        </label>
        <label>
          Contraseña del panel (plaintext para hashing en backend)
          <input
            type="password"
            name="auth_password"
            value={state.auth_password}
            onChange={handleChange}
            placeholder="Contraseña temporal"
          />
        </label>
        <button type="submit" className="primary">
          Guardar cambios
        </button>
        {status && <p className="status success">{status}</p>}
      </form>
    </section>
  );
}
