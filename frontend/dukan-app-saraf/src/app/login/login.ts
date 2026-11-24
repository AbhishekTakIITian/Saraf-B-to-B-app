import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../services';
import { ThemeToggleComponent } from '../theme-toggle/theme-toggle';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, ThemeToggleComponent],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class LoginComponent {
  // ── Main login form ──────────────────────────────────────────────────
  username = '';
  password = '';
  loading  = signal(false);
  errorMsg = signal('');
  showPwd  = signal(false);

  // ── Admin verify modal (shown when "Create User" is clicked) ─────────
  showVerifyModal  = signal(false);
  adminUsername    = '';
  adminPassword    = '';
  verifyLoading    = signal(false);
  verifyError      = signal('');
  showAdminPwd     = signal(false);

  constructor(
    private api: ApiService,
    private router: Router,
  ) {}

  // ── Helpers ──────────────────────────────────────────────────────────
  togglePassword(): void      { this.showPwd.set(!this.showPwd()); }
  toggleAdminPwd(): void      { this.showAdminPwd.set(!this.showAdminPwd()); }

  // ── Main login submit ────────────────────────────────────────────────
  onSubmit(): void {
    if (!this.username.trim() || !this.password.trim()) {
      this.errorMsg.set('Please enter both username and password.');
      return;
    }
    this.loading.set(true);
    this.errorMsg.set('');

    this.api.login({ username: this.username, password: this.password }).subscribe({
      next: (res) => {
        this.loading.set(false);
        sessionStorage.setItem('user', this.username);
        sessionStorage.setItem('role', res.role);
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        if (err.status === 401)      this.errorMsg.set('Invalid username or password.');
        else if (err.status === 0)   this.errorMsg.set('Cannot reach the server. Make sure the backend is running on port 8000.');
        else                         this.errorMsg.set(err.error?.detail ?? 'An unexpected error occurred.');
      },
    });
  }

  // ── Create User button ───────────────────────────────────────────────
  openVerifyModal(): void {
    this.adminUsername = '';
    this.adminPassword = '';
    this.verifyError.set('');
    this.showVerifyModal.set(true);
  }

  closeVerifyModal(): void {
    this.showVerifyModal.set(false);
  }

  // ── Admin credential verification ─────────────────────────────────────
  verifyAdmin(): void {
    if (!this.adminUsername.trim() || !this.adminPassword.trim()) {
      this.verifyError.set('Please enter admin username and password.');
      return;
    }
    this.verifyLoading.set(true);
    this.verifyError.set('');

    this.api.login({ username: this.adminUsername, password: this.adminPassword }).subscribe({
      next: (res) => {
        this.verifyLoading.set(false);
        if (res.role !== 'admin') {
          this.verifyError.set('Access denied. Only admin accounts can create users.');
          return;
        }
        // Store verified admin in session and navigate to create-user page
        sessionStorage.setItem('adminUser', this.adminUsername);
        this.showVerifyModal.set(false);
        this.router.navigate(['/create-user']);
      },
      error: (err) => {
        this.verifyLoading.set(false);
        if (err.status === 401)    this.verifyError.set('Invalid admin credentials.');
        else if (err.status === 0) this.verifyError.set('Cannot reach the server.');
        else                       this.verifyError.set(err.error?.detail ?? 'An unexpected error occurred.');
      },
    });
  }
}
