import { Injectable, signal } from '@angular/core';

export type ThemeMode = 'light' | 'dark';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly theme = signal<ThemeMode>(this.getInitialTheme());

  constructor() {
    this.applyTheme(this.theme());
  }

  toggle(): void {
    const next: ThemeMode = this.theme() === 'dark' ? 'light' : 'dark';
    this.setTheme(next);
  }

  setTheme(theme: ThemeMode): void {
    this.theme.set(theme);
    this.applyTheme(theme);
    try {
      localStorage.setItem('theme', theme);
    } catch {
      // ignore storage errors
    }
  }

  private getInitialTheme(): ThemeMode {
    try {
      const stored = localStorage.getItem('theme');
      if (stored === 'light' || stored === 'dark') {
        return stored;
      }
    } catch {
      // ignore storage errors
    }
    return 'dark';
  }

  private applyTheme(theme: ThemeMode): void {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme);
    }
  }
}
