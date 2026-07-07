import { ReactNode, useLayoutEffect, useRef, useState } from "react";
import { ChevronIcon } from "./icons";

export type PanelTone = "income" | "savings" | "taxes" | "spending";

interface CollapsiblePanelProps {
  title: string;
  subtitle?: string;
  tone: PanelTone;
  // Shown (tone-colored) in the header while collapsed, e.g. "$0/mo".
  collapsedSummary?: ReactNode;
  children: ReactNode;
}

// Trickle-down panel shell: colored left border, clickable header that
// collapses the body with a measured-height animation, and a rotating
// caret. Tone drives the accent color via a `--tone` CSS variable.
export default function CollapsiblePanel({
  title,
  subtitle,
  tone,
  collapsedSummary,
  children,
}: CollapsiblePanelProps) {
  const [collapsed, setCollapsed] = useState(false);
  const bodyInnerRef = useRef<HTMLDivElement>(null);
  const [bodyHeight, setBodyHeight] = useState(0);
  useLayoutEffect(() => {
    if (bodyInnerRef.current) setBodyHeight(bodyInnerRef.current.scrollHeight);
  });
  const toggle = () => setCollapsed((value) => !value);

  return (
    <section className={`panel panel-${tone}`}>
      <div
        className="panel-header"
        role="button"
        tabIndex={0}
        aria-expanded={!collapsed}
        onClick={toggle}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            toggle();
          }
        }}
      >
        <div className="panel-head-left">
          <h3 className="panel-title">{title}</h3>
          {!collapsed && subtitle && <p className="panel-sub">{subtitle}</p>}
        </div>
        <div className="panel-head-right">
          {collapsed && collapsedSummary && (
            <div className="panel-collapsed">{collapsedSummary}</div>
          )}
          <span className={`panel-caret${collapsed ? " inverted" : ""}`}>
            <ChevronIcon />
          </span>
        </div>
      </div>

      <div className="panel-body" style={{ height: collapsed ? 0 : bodyHeight }}>
        <div className="panel-body-inner" ref={bodyInnerRef}>
          {children}
        </div>
      </div>
    </section>
  );
}
