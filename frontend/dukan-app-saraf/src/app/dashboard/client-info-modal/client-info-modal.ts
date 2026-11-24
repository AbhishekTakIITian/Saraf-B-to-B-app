import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Client } from '../../services';

@Component({
  selector: 'app-client-info-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './client-info-modal.html',
  styleUrl: './client-info-modal.scss',
})
export class ClientInfoModalComponent {
  @Input({ required: true }) client!: Client;
  @Output() close = new EventEmitter<void>();

  onClose(): void {
    this.close.emit();
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
    return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
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
