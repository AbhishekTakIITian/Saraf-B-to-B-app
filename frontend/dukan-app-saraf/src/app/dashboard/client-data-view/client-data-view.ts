import { Component, EventEmitter, Input, OnInit, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ApiService,
  Client,
  ClientDataEntry,
  ClientDataCreate,
  ClientDataUpdate,
} from '../../services';
import { ThemeToggleComponent } from '../../theme-toggle/theme-toggle';

@Component({
  selector: 'app-client-data-view',
  standalone: true,
  imports: [CommonModule, FormsModule, ThemeToggleComponent],
  templateUrl: './client-data-view.html',
  styleUrl: './client-data-view.scss',
})
export class ClientDataViewComponent implements OnInit {
  @Input({ required: true }) client!: Client;
  @Input({ required: true }) username!: string;
  @Output() close = new EventEmitter<void>();

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

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadClientData();
  }

  loadClientData(): void {
    this.dataLoading.set(true);
    this.dataError.set('');
    this.api.getClientData(this.client.id, this.username).subscribe({
      next: (entries) => {
        this.clientData.set(entries);
        this.dataLoading.set(false);
      },
      error: (err) => {
        this.dataLoading.set(false);
        this.dataError.set(err.error?.detail ?? 'Failed to load client data entries.');
      },
    });
  }

  onBack(): void {
    this.close.emit();
  }

  // ── Add Entry Modal ────────────────────────────────────────────────

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
      this.addDataError.set('All fields are required.');
      return;
    }

    this.addDataLoading.set(true);
    this.addDataError.set('');

    const payload: ClientDataCreate = {
      number: Number(this.newEntryNumber),
      jwellery_value: Number(this.newEntryJwelleryValue),
      description: this.newEntryDescription.trim(),
    };

    this.api.createClientData(this.client.id, payload, this.username).subscribe({
      next: () => {
        this.addDataLoading.set(false);
        this.closeAddDataModal();
        this.loadClientData();
      },
      error: (err) => {
        this.addDataLoading.set(false);
        this.addDataError.set(err.error?.detail ?? 'Failed to create data entry.');
      },
    });
  }

  // ── Complete Data Entry Modal ──────────────────────────────────────

  openCompleteModal(event: Event, entry: ClientDataEntry): void {
    event.stopPropagation();
    this.completingEntry.set(entry);
    this.completeFinalValue = null;
    this.completeError.set('');
  }

  closeCompleteModal(): void {
    this.completingEntry.set(null);
  }

  submitCompleteEntry(): void {
    const entry = this.completingEntry();
    if (!entry) return;

    if (this.completeFinalValue === null || isNaN(this.completeFinalValue)) {
      this.completeError.set('Final value is required to complete the entry.');
      return;
    }

    this.completeLoading.set(true);
    this.completeError.set('');

    const payload: ClientDataUpdate = {
      final_value: Number(this.completeFinalValue),
    };

    this.api.updateClientData(this.client.id, entry.id, payload, this.username).subscribe({
      next: () => {
        this.completeLoading.set(false);
        this.closeCompleteModal();
        this.loadClientData();
      },
      error: (err) => {
        this.completeLoading.set(false);
        this.completeError.set(err.error?.detail ?? 'Failed to complete data entry.');
      },
    });
  }

  // ── Edit Data Entry Modal ──────────────────────────────────────────

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
    if (!entry) return;

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

    this.api.updateClientData(this.client.id, entry.id, payload, this.username).subscribe({
      next: () => {
        this.editDataLoading.set(false);
        this.closeEditModal();
        this.loadClientData();
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
    this.api.deleteClientData(this.client.id, entryId, this.username).subscribe({
      next: () => {
        this.clientData.update((list) => list.filter((e) => e.id !== entryId));
      },
      error: (err) => {
        this.dataError.set(err.error?.detail ?? 'Failed to delete data entry.');
      },
    });
  }

  // ── Formatters ─────────────────────────────────────────────────────

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

  formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '—';
    return date.toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
