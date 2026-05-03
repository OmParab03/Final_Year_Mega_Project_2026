import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SkinAnalysis } from './skin-analysis';

describe('SkinAnalysis', () => {
  let component: SkinAnalysis;
  let fixture: ComponentFixture<SkinAnalysis>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SkinAnalysis],
    }).compileComponents();

    fixture = TestBed.createComponent(SkinAnalysis);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
