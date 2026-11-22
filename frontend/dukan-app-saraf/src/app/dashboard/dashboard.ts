import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService, Client, ClientStats, ClientCreate } from '../services';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class DashboardComponent implements OnInit {
  username = '';
  role = '';

  stats = signal<ClientStats | null>(null);
  clients = signal<Client[]>([]);
  loading = signal(true);
  error = signal('');

  // Add Client Modal
  showAddModal = signal(false);
  addLoading = signal(false);
  addError = signal('');
  addSuccess = signal('');
  newName = '';
  newAddress = '';
  newContact = '';

  // Active / Viewed Client Detail Modal
  selectedClient = signal<Client | null>(null);

  // Deletion confirm
  deletingId = signal<number | null>(null);

  constructor(
    private api: ApiService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    const user = sessionStorage.getItem('user');
    if (!user) {
      this.router.navigate(['/login']);
      return;
    }
    this.username = user;
    this.role = sessionStorage.getItem('role') ?? 'user';
    this.loadAll();
  }

  loadAll(): void {
    this.loading.set(true);
    this.error.set('');

    this.api.getClientStats(this.username).subscribe({
      next: (s) => this.stats.set(s),
      error: () => {},
    });

    this.api.listClients(this.username).subscribe({
      next: (list) => {
        this.clients.set(list);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err.error?.detail ?? 'Failed to load clients.');
      },
    });
  }

  refreshStats(): void {
    this.api.getClientStats(this.username).subscribe({
      next: (s) => this.stats.set(s),
      error: () => {},
    });
  }

  getInitial(name: string): string {
    if (!name) return '?';
    const trimmed = name.trim();
    return trimmed.charAt(0).toUpperCase();
  }

  getAvatarBackground(name: string): string {
    const gradients = [
      'linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%)',
      'linear-gradient(135deg, #EC4899 0%, #D946EF 100%)',
      'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)',
      'linear-gradient(135deg, #F59E0B 0%, #EA580C 100%)',
      'linear-gradient(135deg, #10B981 0%, #059669 100%)',
      'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)',
      'linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)',
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const idx = Math.abs(hash) % gradients.length;
    return gradients[idx];
  }

  formatRelative(dateStr: string | null | undefined): string {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '—';
    const diff = Date.now() - date.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days < 30) return `${days}d ago`;
    return date.toLocaleDateString();
  }

  openAddModal(): void {
    this.newName = '';
    this.newAddress = '';
    this.newContact = '';
    this.addError.set('');
    this.addSuccess.set('');
    this.showAddModal.set(true);
  }

  closeAddModal(): void {
    this.showAddModal.set(false);
  }

  submitAddClient(): void {
    if (!this.newName.trim()) {
      this.addError.set('Client name is required.');
      return;
    }

    this.addLoading.set(true);
    this.addError.set('');

    const payload: ClientCreate = {
      name: this.newName.trim(),
      address: this.newAddress.trim() || undefined,
      contact_number: this.newContact.trim() || undefined,
    };

    this.api.createClient(payload, this.username).subscribe({
      next: (created) => {
        this.addLoading.set(false);
        this.clients.update((current) => [created, ...current]);
        this.stats.update((s) => ({
          total: (s?.total ?? 0) + 1,
          last_edited: created,
          last_accessed: s?.last_accessed ?? null,
        }));
        this.addSuccess.set(`Client "${created.name}" created successfully!`);
        setTimeout(() => this.closeAddModal(), 900);
      },
      error: (err) => {
        this.addLoading.set(false);
        this.addError.set(err.error?.detail ?? 'Failed to create client.');
      },
    });
  }

  onClientClick(client: Client): void {
    // Record access on backend
    this.api.getClient(client.id, this.username).subscribe({
      next: (updatedClient) => {
        this.selectedClient.set(updatedClient);
        this.refreshStats();
      },
      error: () => {
        this.selectedClient.set(client);
      },
    });
  }

  closeDetailModal(): void {
    this.selectedClient.set(null);
  }

  confirmDelete(event: Event, id: number): void {
    event.stopPropagation();
    this.deletingId.set(id);
  }

  cancelDelete(event: Event): void {
    event.stopPropagation();
    this.deletingId.set(null);
  }

  deleteClient(event: Event, id: number): void {
    event.stopPropagation();
    this.api.deleteClient(id, this.username).subscribe({
      next: () => {
        this.clients.update((list) => list.filter((c) => c.id !== id));
        this.deletingId.set(null);
        this.refreshStats();
      },
      error: () => {
        this.deletingId.set(null);
      },
    });
  }

  logout(): void {
    sessionStorage.clear();
    this.router.navigate(['/login']);
  }
}
