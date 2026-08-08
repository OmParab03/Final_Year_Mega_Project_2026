import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.html',
  styleUrl: './home.css'
})
export class HomeComponent implements OnInit {

  // Stats
  totalScans: number = 0;
  totalReports: number = 0;
  skinScore: number = 0;

  // Upload state
  previewUrl: string | null = null;
  selectedFile: File | null = null;
  isDragging: boolean = false;
  analyzing: boolean = false;
  errorMessage: string = '';

  // Recent history
  recentHistory: any[] = [];

  constructor(private router: Router) {}

  ngOnInit() {
    this.loadStats();
  }

  loadStats() {
    // Placeholder - connect to your backend
    this.totalScans = 0;
    this.totalReports = 0;
    this.skinScore = 0;
    this.recentHistory = [];
  }

  // ==================== FILE UPLOAD ====================
  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.processFile(input.files[0]);
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
      this.processFile(event.dataTransfer.files[0]);
    }
  }

  processFile(file: File) {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      this.errorMessage = 'Please upload a JPG, PNG, or WEBP image.';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage = 'File size must be less than 10MB.';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    this.selectedFile = file;
    const reader = new FileReader();
    reader.onload = () => {
      this.previewUrl = reader.result as string;
    };
    reader.readAsDataURL(file);
  }

  removeImage() {
    this.previewUrl = null;
    this.selectedFile = null;
  }

  analyzeImage() {
    if (!this.selectedFile) return;
    this.analyzing = true;
    setTimeout(() => {
      this.analyzing = false;
      this.router.navigate(['/dashboard/ingredient-analysis']);
    }, 1500);
  }

  goToHistory() {
    this.router.navigate(['/dashboard/history']);
  }
}