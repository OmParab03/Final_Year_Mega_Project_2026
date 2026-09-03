import { Component, ChangeDetectorRef, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../auth/auth.service';

export interface SkinCondition {
  label: string;
  confidence: number | null;
}

export interface AnalysisHistoryItem {
  id: string;
  thumbnail: string;
  date: string;
  result: string;
  severity: 'low' | 'medium' | 'high';
}

@Component({
  selector: 'app-skin-analysis',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './skin-analysis.html',
  styleUrls: ['./skin-analysis.css']
})
export class SkinAnalysis implements OnInit {
  // Upload state
  previewUrl: string | null = null;
  selectedFile: File | null = null;
  isDragging: boolean = false;
  analyzing: boolean = false;
  errorMessage: string = '';

  // Results
  showResults: boolean = false;
  result: { skinType: string; conditions: SkinCondition[] } = {
    skinType: '',
    conditions: []
  };

  // History (merged in below the upload/results section)
  historyList: AnalysisHistoryItem[] = [];
  historyLoading: boolean = true;

  constructor(private authService: AuthService, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    this.loadHistory();
  }

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
      this.cdr.markForCheck();
      setTimeout(() => {
        this.errorMessage = '';
        this.cdr.markForCheck();
      }, 3000);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage = 'File size must be less than 10MB.';
      this.cdr.markForCheck();
      setTimeout(() => {
        this.errorMessage = '';
        this.cdr.markForCheck();
      }, 3000);
      return;
    }

    this.selectedFile = file;
    this.showResults = false;
    const reader = new FileReader();
    reader.onload = () => {
      this.previewUrl = reader.result as string;
      // FileReader callbacks run outside Angular's change-detection scheduler
      // (this app uses zoneless CD), so the view won't refresh on its own here.
      this.cdr.markForCheck();
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
    this.errorMessage = '';

    this.authService.analyzeSkin(this.selectedFile).subscribe({
      next: (res) => {
        this.analyzing = false;
        this.showResults = true;
        const analysis = res.analysis;
        this.result = {
          skinType: analysis.skinType || 'Unknown',
          conditions: analysis.conditions || []
        };
        this.cdr.markForCheck();
        this.loadHistory(); // refresh the list below with the scan we just saved
      },
      error: (err) => {
        this.analyzing = false;
        this.errorMessage = err?.error?.message || 'Analysis failed. Please try again.';
        this.cdr.markForCheck();
        setTimeout(() => {
          this.errorMessage = '';
          this.cdr.markForCheck();
        }, 4000);
      }
    });
  }

  loadHistory() {
    this.historyLoading = true;
    this.authService.getAnalysisHistory().subscribe({
      next: (res) => {
        this.historyList = (res.history || []).map((item: any) => ({
          id: item.id,
          thumbnail: item.imageUrl?.startsWith('/uploads/')
            ? `${this.authService.apiOrigin}${item.imageUrl}`
            : item.imageUrl,
          date: new Date(item.createdAt).toLocaleDateString(),
          result: item.result,
          severity: item.severity
        }));
        this.historyLoading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.historyList = [];
        this.historyLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  /** Turns a raw 0-1 confidence into a plain-language qualifier for the UI. */
  confidenceLabel(confidence: number | null): string {
    if (confidence === null || confidence === undefined) return '';
    if (confidence >= 0.75) return 'high confidence';
    if (confidence >= 0.5) return 'moderate confidence';
    return 'low confidence';
  }
}
