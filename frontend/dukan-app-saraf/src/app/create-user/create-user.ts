import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../services';

@Component({
  selector: 'app-create-user',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './create-user.html',
  styleUrl: './create-user.scss',
})
export class CreateUserComponent implements OnInit {
  // Form fields
  newUsername  = '';
  newPassword  = '';
  confirmPwd   = '';
  role: 'user' = 'user';

  // UI state
  loading      = signal(false);
  errorMsg     = signal('');
  successMsg   = signal('');
  showPwd      = signal(false);
  showConfirm  = signal(false);

  // The verified admin who was redirected here
  adminUser    = '';

  constructor(
    private api: ApiService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    // Guard: if no admin session, redirect back to login
    const admin = sessionStorage.getItem('adminUser');
    if (!admin) {
      this.router.navigate(['/login']);
      return;
    }
    this.adminUser = admin;
  }

  togglePwd():     void { this.showPwd.set(!this.showPwd()); }
  toggleConfirm(): void { this.showConfirm.set(!this.showConfirm()); }

  goBack(): void {
    sessionStorage.removeItem('adminUser');
    this.router.navigate(['/login']);
  }

  onSubmit(): void {
    this.errorMsg.set('');
    this.successMsg.set('');

    // Client-side validation
    if (!this.newUsername.trim()) {
      this.errorMsg.set('Username is required.'); return;
    }
    if (this.newPassword.length < 3) {
      this.errorMsg.set('Password must be at least 3 characters.'); return;
    }
    if (this.newPassword !== this.confirmPwd) {
      this.errorMsg.set('Passwords do not match.'); return;
    }

    this.loading.set(true);

    this.api
      .addUser(
        { username: this.newUsername, password: this.newPassword, role: this.role },
        this.adminUser,
      )
      .subscribe({
        next: (res) => {
          this.loading.set(false);
          this.successMsg.set(res.message);
          // Reset form
          this.newUsername = '';
          this.newPassword = '';
          this.confirmPwd  = '';
          this.role        = 'user';
        },
        error: (err) => {
          this.loading.set(false);
          if (err.status === 403)      this.errorMsg.set('Permission denied. Admin access required.');
          else if (err.status === 409) this.errorMsg.set(`Username "${this.newUsername}" already exists.`);
          else if (err.status === 0)   this.errorMsg.set('Cannot reach the server.');
          else                         this.errorMsg.set(err.error?.detail ?? 'An unexpected error occurred.');
        },
      });
  }
}
