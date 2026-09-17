import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Dashboard } from './dashboard';

describe('Dashboard', () => {
  let component: Dashboard;
  let fixture: ComponentFixture<Dashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        Dashboard,
        HttpClientTestingModule,
        RouterTestingModule
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Dashboard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should return correct greeting', () => {
    const greeting = component.getGreeting();
    expect(['Morning', 'Afternoon', 'Evening']).toContain(greeting);
  });

  it('should default to dashboard tab', () => {
    expect(component.activeTab).toBe('dashboard');
  });

  it('should remove image on removeImage()', () => {
    component.previewUrl = 'test-url';
    component.selectedFile = new File([''], 'test.jpg');
    component.removeImage();
    expect(component.previewUrl).toBeNull();
    expect(component.selectedFile).toBeNull();
  });
});