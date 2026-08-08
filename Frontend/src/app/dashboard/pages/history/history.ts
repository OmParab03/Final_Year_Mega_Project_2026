import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

export interface HistoryItem {
  id: string;
  thumbnail: string;
  date: string;
  result: string;
  severity: 'low' | 'medium' | 'high';
}

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './history.html',
  styleUrl: './history.css'
})
export class HistoryComponent implements OnInit {
  historyList: HistoryItem[] = [];
  loading: boolean = true;

  constructor(private router: Router) {}

  ngOnInit() {
    this.loadHistory();
  }

  loadHistory() {
    // Placeholder - connect to your backend
    this.loading = false;
    this.historyList = [];
  }

  goToDashboard() {
    this.router.navigate(['/dashboard']);
  }

  goToAnalysis() {
    this.router.navigate(['/dashboard/skin-analysis']);
  }
}