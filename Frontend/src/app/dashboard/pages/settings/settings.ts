import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.html',
  styleUrl: './settings.css'
})
export class SettingsComponent {
  settings = {
    emailNotifications: true,
    saveHistory: true,
    darkMode: false
  };

  successMessage: string = '';

  constructor(private cdr: ChangeDetectorRef) {}

  saveSettings() {
    // Placeholder - connect to your backend
    this.successMessage = 'Settings saved successfully!';
    this.cdr.markForCheck();
    setTimeout(() => {
      this.successMessage = '';
      this.cdr.markForCheck();
    }, 3000);
  }
}
