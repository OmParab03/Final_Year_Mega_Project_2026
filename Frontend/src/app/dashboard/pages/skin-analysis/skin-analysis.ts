import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-skin-analysis',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './skin-analysis.html',
  styleUrls: ['./skin-analysis.css']
})
export class SkinAnalysis {
  // Upload state
  previewUrl: string | null = null;
  selectedFile: File | null = null;
  isDragging: boolean = false;
  analyzing: boolean = false;
  errorMessage: string = '';

  // Results
  showResults: boolean = false;
  result = {
    skinType: '',
    acne: '',
    redness: '',
    moisture: '',
    score: 0
  };

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
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      this.errorMessage = 'Please upload a JPG, PNG, or WEBP image.';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage = 'File size must be less than 10MB.';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    this.selectedFile = file;
    this.showResults = false;
    const reader = new FileReader();
    reader.onload = () => {
      this.previewUrl = reader.result as string;
    };
    reader.readAsDataURL(file);
  }

  removeImage() {
    this.previewUrl = null;
    this.selectedFile = null;
    this.showResults = false;
  }

  analyzeSkin() {
    if (!this.selectedFile) return;
    this.analyzing = true;
    this.showResults = false;

    // Simulate API call - replace with real backend call
    setTimeout(() => {
      this.analyzing = false;
      this.showResults = true;
      this.result = {
        skinType: 'Oily',
        acne: 'Medium',
        redness: 'Low',
        moisture: 'Normal',
        score: 72
      };
    }, 2000);
  }
}