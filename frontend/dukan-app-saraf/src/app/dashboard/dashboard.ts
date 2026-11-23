import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  ApiService,
  Client,
  ClientStats,
  ClientCreate,
  ClientDataEntry,
  ClientDataCreate,
  ClientDataUpdate,
  CompleteDataEntry,
} from '../services';

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

  // ── Add Client Modal ───────────────────────────────────────────────
  showAddModal = signal(false);
  addLoading = signal(false);
  addError = signal('');
  addSuccess = signal('');
  newName = '';
  newAddress = '';
  newContact = '';

  // ── Client Info Popup (ⓘ button) ──────────────────────────────────
  infoClient = signal<Client | null>(null);

  // ── Client Data View (card click → full data view) ─────────────────
  activeClient = signal<Client | null>(null);
  clientData = signal<ClientDataEntry[]>([]);
  dataLoading = signal(false);
  dataError = signal('');

  // ── Add Data Entry Modal ───────────────────────────────────────────
  showAddDataModal = signal(false);
  addDataLoading = signal(false);
  addDataError = signal('');
  newEntryNumber: number | null = null;
  newEntryJwelleryValue: number | null = null;
  newEntryDescription = '';

  // ── Complete Data Entry Modal ──────────────────────────────────────
  completingEntry = signal<ClientDataEntry | null>(null);
  completeFinalValue: number | null = null;
  completeLoading = signal(false);
  completeError = signal('');

  // ── Edit Data Entry Modal ──────────────────────────────────────────
  editingEntry = signal<ClientDataEntry | null>(null);
  editEntryNumber: number | null = null;
  editEntryJwelleryValue: number | null = null;
  editEntryDescription = '';
  editEntryFinalValue: number | null = null;
  editDataLoading = signal(false);
  editDataError = signal('');

  // ── Deletion confirm (client card) ────────────────────────────────
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
    return name.trim().charAt(0).toUpperCase();
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
    return gradients[Math.abs(hash) % gradients.length];
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

  formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  // ── Add Client Modal ───────────────────────────────────────────────

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

  // ── Client Info Popup (ⓘ) ─────────────────────────────────────────

  openInfoPopup(event: Event, client: Client): void {
    event.stopPropagation();
    this.infoClient.set(client);
  }

  closeInfoPopup(): void {
    this.infoClient.set(null);
  }

  // ── Client Data View ───────────────────────────────────────────────

  onClientClick(client: Client): void {
    this.activeClient.set(client);
    this.dataError.set('');
    this.dataLoading.set(true);
    this.clientData.set([]);

    // Record backend access
    this.api.getClient(client.id, this.username).subscribe({
      next: (updated) => {
        this.activeClient.set(updated);
        this.refreshStats();
      },
      error: () => {},
    });

    this.loadClientData(client.id);
  }

  loadClientData(clientId: number): void {
    this.api.getClientData(clientId, this.username).subscribe({
      next: (data) => {
        this.clientData.set(data);
        this.dataLoading.set(false);
      },
      error: (err) => {
        this.dataLoading.set(false);
        this.dataError.set(err.error?.detail ?? 'Failed to load data entries.');
      },
    });
  }

  closeDataView(): void {
    this.activeClient.set(null);
    this.clientData.set([]);
    this.dataError.set('');
  }

  // ── Add Data Entry (Only number, jewellery_value, description) ──────

  openAddDataModal(): void {
    this.newEntryNumber = null;
    this.newEntryJwelleryValue = null;
    this.newEntryDescription = '';
    this.addDataError.set('');
    this.showAddDataModal.set(true);
  }

  closeAddDataModal(): void {
    this.showAddDataModal.set(false);
  }

  submitAddDataEntry(): void {
    if (this.newEntryNumber === null || this.newEntryJwelleryValue === null) {
      this.addDataError.set('Number, jewellery value, and description are required.');
      return;
    }

    const client = this.activeClient();
    if (!client) return;

    this.addDataLoading.set(true);
    this.addDataError.set('');

    const payload: ClientDataCreate = {
      number: this.newEntryNumber,
      jwellery_value: this.newEntryJwelleryValue,
      description: this.newEntryDescription.trim(),
    };

    this.api.createClientData(client.id, payload, this.username).subscribe({
      next: () => {
        this.addDataLoading.set(false);
        this.closeAddDataModal();
        this.loadClientData(client.id);
      },
      error: (err) => {
        this.addDataLoading.set(false);
        this.addDataError.set(err.error?.detail ?? 'Failed to create entry.');
      },
    });
  }

  // ── Complete Data Entry (Final Value input + calls complete/update API) ──

  openCompleteModal(event: Event, entry: ClientDataEntry): void {
    event.stopPropagation();
    this.completingEntry.set(entry);
    this.completeFinalValue = entry.final_value ?? null;
    this.completeError.set('');
  }

  closeCompleteModal(): void {
    this.completingEntry.set(null);
  }

  submitCompleteEntry(): void {
    const entry = this.completingEntry();
    const client = this.activeClient();
    if (!entry || !client) return;

    if (this.completeFinalValue === null || isNaN(this.completeFinalValue)) {
      this.completeError.set('Final value is required to complete the entry.');
      return;
    }

    this.completeLoading.set(true);
    this.completeError.set('');

    const payload: ClientDataUpdate = {
      final_value: Number(this.completeFinalValue),
    };

    this.api.updateClientData(client.id, entry.id, payload, this.username).subscribe({
      next: () => {
        this.completeLoading.set(false);
        this.closeCompleteModal();
        this.loadClientData(client.id);
      },
      error: (err) => {
        this.completeLoading.set(false);
        this.completeError.set(err.error?.detail ?? 'Failed to complete data entry.');
      },
    });
  }

  // ── Edit Data Entry (Row Click) ────────────────────────────────────

  openRowEditModal(entry: ClientDataEntry): void {
    this.editingEntry.set(entry);
    this.editEntryNumber = entry.number;
    this.editEntryJwelleryValue = entry.jwellery_value;
    this.editEntryDescription = entry.description;
    this.editEntryFinalValue = entry.final_value;
    this.editDataError.set('');
  }

  closeEditModal(): void {
    this.editingEntry.set(null);
  }

  submitEditEntry(): void {
    const entry = this.editingEntry();
    const client = this.activeClient();
    if (!entry || !client) return;

    if (this.editEntryNumber === null || this.editEntryJwelleryValue === null || !this.editEntryDescription.trim()) {
      this.editDataError.set('Number, jewellery value, and description are required.');
      return;
    }

    this.editDataLoading.set(true);
    this.editDataError.set('');

    const payload: ClientDataUpdate = {
      number: this.editEntryNumber,
      jwellery_value: this.editEntryJwelleryValue,
      description: this.editEntryDescription.trim(),
      ...(entry.date_completed ? { final_value: this.editEntryFinalValue ?? undefined } : {}),
    };

    this.api.updateClientData(client.id, entry.id, payload, this.username).subscribe({
      next: () => {
        this.editDataLoading.set(false);
        this.closeEditModal();
        this.loadClientData(client.id);
      },
      error: (err) => {
        this.editDataLoading.set(false);
        this.editDataError.set(err.error?.detail ?? 'Failed to update entry.');
      },
    });
  }

  // ── Delete Data Row ────────────────────────────────────────────────

  deleteDataEntry(event: Event, entryId: number): void {
    event.stopPropagation();
    const client = this.activeClient();
    if (!client) return;

    this.api.deleteClientData(client.id, entryId, this.username).subscribe({
      next: () => {
        this.clientData.update((list) => list.filter((e) => e.id !== entryId));
      },
      error: (err) => {
        this.dataError.set(err.error?.detail ?? 'Failed to delete data entry.');
      },
    });
  }

  // ── Delete Client ──────────────────────────────────────────────────

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
