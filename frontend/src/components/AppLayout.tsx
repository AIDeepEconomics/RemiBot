import { NavLink } from "react-router-dom";
import type { PropsWithChildren } from "react";

const navItems = [
  { to: "/", label: "Inicio" },
  { to: "/remitos", label: "Remitos" },
  { to: "/configuracion", label: "Configuración" },
  { to: "/documentacion", label: "Documentación" },
  { to: "/logs", label: "Logs" }
];

export function AppLayout({ children }: PropsWithChildren): JSX.Element {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">RemiBOT</div>
        <nav>
          <ul>
            {navItems.map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} end>
                  {({ isActive }) => (
                    <span className={isActive ? "active" : undefined}>{item.label}</span>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
