"use client";

import { useState } from "react";

interface GlassSelectOption {
  value: string;
  label: string;
}

interface GlassSelectProps {
  id: string;
  value: string;
  options: GlassSelectOption[];
  placeholder?: string;
  onChange: (value: string) => void;
}

export function GlassSelect({ id, value, options, placeholder = "Choose an option", onChange }: GlassSelectProps) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(Math.max(0, options.findIndex((option) => option.value === value)));
  const selected = options.find((option) => option.value === value);

  function choose(option: GlassSelectOption) {
    onChange(option.value);
    setActiveIndex(options.indexOf(option));
    setOpen(false);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "Escape") {
      setOpen(false);
      return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      const direction = event.key === "ArrowDown" ? 1 : -1;
      setActiveIndex((index) => (index + direction + options.length) % options.length);
      return;
    }
    if (event.key === "Enter" && open) {
      event.preventDefault();
      choose(options[activeIndex]);
    }
  }

  return <div className={`glass-select ${open ? "is-open" : ""}`} onBlur={() => window.setTimeout(() => setOpen(false), 120)}>
    <button id={id} type="button" className="glass-select-trigger" aria-haspopup="listbox" aria-expanded={open} aria-controls={`${id}-options`} aria-activedescendant={open ? `${id}-option-${activeIndex}` : undefined} onClick={() => setOpen((current) => !current)} onKeyDown={handleKeyDown}>
      <span>{selected?.label || placeholder}</span><span className="glass-select-chevron" aria-hidden="true">⌄</span>
    </button>
    {open && <div className="glass-select-panel glass" id={`${id}-options`} role="listbox" aria-label={placeholder}>
      {options.map((option, index) => <button key={option.value} id={`${id}-option-${index}`} type="button" role="option" aria-selected={option.value === value} className={`glass-select-option ${index === activeIndex ? "is-active" : ""}`} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(option)}><span>{option.label}</span>{option.value === value && <span className="glass-select-check" aria-hidden="true">✓</span>}</button>)}
    </div>}
  </div>;
}
