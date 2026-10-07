"use client";

import { useState } from "react";

interface SuggestionInputProps {
  suggestions: string[];
  value: string;
  onChange: (value: string) => void;
}

interface SkillSuggestionInputProps {
  suggestions: string[];
  selected: string[];
  onAdd: (skill: string) => void;
}

function matches(suggestions: string[], query: string, excluded: string[] = []) {
  const normalized = query.trim().toLocaleLowerCase();
  const excludedSet = new Set(excluded.map((item) => item.toLocaleLowerCase()));
  return suggestions
    .filter((item) => !excludedSet.has(item.toLocaleLowerCase()) && item.toLocaleLowerCase().includes(normalized))
    .slice(0, 8);
}

export function RoleSuggestionInput({ suggestions, value, onChange }: SuggestionInputProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const options = open && query.trim() ? matches(suggestions, query) : [];
  const customRole = query.trim() && !suggestions.some((role) => role.toLocaleLowerCase() === query.trim().toLocaleLowerCase());
  const optionCount = options.length + Number(Boolean(customRole));

  function choose(role: string) {
    onChange(role);
    setQuery("");
    setOpen(false);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (!optionCount || !open) {
      if (event.key === "Enter") setOpen(false);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) => (index + 1) % optionCount);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => (index - 1 + optionCount) % optionCount);
    } else if (event.key === "Enter") {
      event.preventDefault();
      choose(activeIndex < options.length ? options[activeIndex] : query.trim());
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  return <div className="suggestion-control" onBlur={() => window.setTimeout(() => setOpen(false), 120)}>
    <input id="target-role" role="combobox" aria-autocomplete="list" aria-expanded={open && optionCount > 0} aria-controls="role-suggestions-list" aria-activedescendant={open ? `role-option-${activeIndex}` : undefined} autoComplete="off" value={value} onFocus={() => { if (query.trim()) setOpen(true); }} onChange={(event) => { onChange(event.target.value); setQuery(event.target.value); setActiveIndex(0); setOpen(Boolean(event.target.value.trim())); }} onKeyDown={handleKeyDown} placeholder="Type a role, e.g. Data analyst" />
    {open && optionCount > 0 && <div className="suggestion-panel glass" id="role-suggestions-list" role="listbox" aria-label="Suggested roles">
      <span className="suggestion-heading">SUGGESTED ROLES</span>
      {options.map((role, index) => <button className={`suggestion-option ${index === activeIndex ? "is-active" : ""}`} id={`role-option-${index}`} role="option" aria-selected={index === activeIndex} key={role} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(role)}><span>{role}</span><span className="suggestion-arrow">↗</span></button>)}
      {customRole && <button className={`suggestion-option suggestion-custom ${activeIndex === options.length ? "is-active" : ""}`} id={`role-option-${options.length}`} role="option" aria-selected={activeIndex === options.length} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(query.trim())}><span>Use “{query.trim()}”</span><span className="suggestion-arrow">↵</span></button>}
    </div>}
  </div>;
}

export function SkillSuggestionInput({ suggestions, selected, onAdd }: SkillSuggestionInputProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const options = open && query.trim() ? matches(suggestions, query, selected) : [];
  const customSkill = query.trim() && !selected.some((skill) => skill.toLocaleLowerCase() === query.trim().toLocaleLowerCase()) && !options.some((skill) => skill.toLocaleLowerCase() === query.trim().toLocaleLowerCase());
  const optionCount = options.length + Number(Boolean(customSkill));

  function choose(skill: string) {
    if (!selected.some((item) => item.toLocaleLowerCase() === skill.toLocaleLowerCase())) onAdd(skill);
    setQuery("");
    setOpen(false);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && optionCount && open) {
      event.preventDefault();
      choose(activeIndex < options.length ? options[activeIndex] : query.trim());
    } else if (event.key === "ArrowDown" && optionCount) {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => (index + 1) % optionCount);
    } else if (event.key === "ArrowUp" && optionCount) {
      event.preventDefault();
      setActiveIndex((index) => (index - 1 + optionCount) % optionCount);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  return <div className="suggestion-control" onBlur={() => window.setTimeout(() => setOpen(false), 120)}>
    <input id="profile-skills" role="combobox" aria-autocomplete="list" aria-expanded={open && optionCount > 0} aria-controls="skill-suggestions-list" aria-activedescendant={open ? `skill-option-${activeIndex}` : undefined} autoComplete="off" value={query} onFocus={() => { if (query.trim()) setOpen(true); }} onChange={(event) => { setQuery(event.target.value); setActiveIndex(0); setOpen(Boolean(event.target.value.trim())); }} onKeyDown={handleKeyDown} placeholder="Start typing a skill, e.g. React" />
    {open && optionCount > 0 && <div className="suggestion-panel glass" id="skill-suggestions-list" role="listbox" aria-label="Suggested skills">
      <span className="suggestion-heading">SKILLS THAT MATCH</span>
      {options.map((skill, index) => <button className={`suggestion-option ${index === activeIndex ? "is-active" : ""}`} id={`skill-option-${index}`} role="option" aria-selected={index === activeIndex} key={skill} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(skill)}><span>{skill}</span><span className="suggestion-add">＋ Add</span></button>)}
      {customSkill && <button className={`suggestion-option suggestion-custom ${activeIndex === options.length ? "is-active" : ""}`} id={`skill-option-${options.length}`} role="option" aria-selected={activeIndex === options.length} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(query.trim())}><span>Add “{query.trim()}” as a skill</span><span className="suggestion-add">＋ Add</span></button>}
    </div>}
  </div>;
}
