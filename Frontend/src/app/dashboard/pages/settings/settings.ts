import { Component } from '@angular/core';
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

  saveSettings() {
    // Placeholder - connect to your backend
    this.successMessage = 'Settings saved successfully!';
    setTimeout(() => this.successMessage = '', 3000);
  }
}