import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';   // ✅ ADD THIS

@Component({
  selector: 'app-skin-analysis',
  standalone: true,
  imports: [CommonModule],   // ✅ ADD THIS
  templateUrl: './skin-analysis.html',
  styleUrls: ['./skin-analysis.css']
})
export class SkinAnalysis {

  selectedImage: any = null;

  result = {
    skinType: '',
    acne: '',
    redness: ''
  };

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedImage = URL.createObjectURL(file);
    }
  }

  analyzeSkin() {
    this.result = {
      skinType: 'Oily',
      acne: 'Medium',
      redness: 'Low'
    };
  }
}