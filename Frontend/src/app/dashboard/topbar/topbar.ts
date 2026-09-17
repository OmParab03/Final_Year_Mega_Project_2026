import { Component, Input, Output, EventEmitter, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './topbar.html',
  styleUrl: './topbar.css'
})
export class TopbarComponent {
  @Input() user: any = null;
  @Input() greeting: string = '';
  @Output() onToggleSidebar = new EventEmitter<void>();
  @Output() onLogout = new EventEmitter<void>();

  showDropdown: boolean = false;

  toggleSidebar() {
    this.onToggleSidebar.emit();
  }

  toggleDropdown() {
    this.showDropdown = !this.showDropdown;
  }

  closeDropdown() {
    this.showDropdown = false;
  }

  logout() {
    this.closeDropdown();
    this.onLogout.emit();
  }

  // Close dropdown when clicking outside
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event) {
    const target = event.target as HTMLElement;
    if (!target.closest('.profile-menu-wrapper')) {
      this.showDropdown = false;
    }
  }
}