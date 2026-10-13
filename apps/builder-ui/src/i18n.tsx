import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import { en, type Key } from './locales/en';
import { ko } from './locales/ko';
import { backendErrors } from './locales/errors';

export type Language = 'en' | 'ko';
export type Translate = (key: Key | string, params?: Record<string, string | number>) => string;
const dictionaries: Record<Language, Record<string, string>> = { en, ko };
const STORAGE = 'factory-language';

function initial(): Language {
  try { const stored = localStorage.getItem(STORAGE); if (stored === 'en' || stored === 'ko') return stored; } catch { /* storage unavailable */ }
  return typeof navigator !== 'undefined' && navigator.language.toLowerCase().startsWith('ko') ? 'ko' : 'en';
}

function format(template: string, params?: Record<string, string | number>) {
  return params ? template.replace(/\{(\w+)\}/g, (match, name) => name in params ? String(params[name]) : match) : template;
}

const I18nContext = createContext<{ language: Language; setLanguage: (language: Language) => void; tr: Translate; translateError: (message: string) => string } | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(initial);
  const setLanguage = useCallback((next: Language) => { setLanguageState(next); try { localStorage.setItem(STORAGE, next); } catch { /* per-viewer convenience only */ } }, []);
  const value = useMemo(() => {
    const dictionary = dictionaries[language];
    const tr: Translate = (key, params) => format(dictionary[key] ?? en[key as Key] ?? String(key), params);
    // Backend messages are English; known ones are translated by exact text or pattern, unknown ones pass through.
    const translateError = (message: string) => {
      if (language === 'en') return message;
      const exact = backendErrors.find(e => e.en === message);
      if (exact) return exact.ko;
      for (const entry of backendErrors) {
        if (entry.pattern) { const match = message.match(entry.pattern); if (match) return format(entry.ko, Object.fromEntries(Object.entries(match.groups ?? {}).map(([k, v]) => [k, v ?? '']))); }
      }
      return message;
    };
    return { language, setLanguage, tr, translateError };
  }, [language, setLanguage]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error('useI18n must be used inside I18nProvider');
  return context;
}

/** Tool status codes stay English in the API and CSS classes; only the label changes. */
export function statusLabel(tr: Translate, status: string | undefined) {
  const key = `status_${(status ?? '').toLowerCase()}`;
  return status && key in en ? tr(key) : status ?? '';
}
