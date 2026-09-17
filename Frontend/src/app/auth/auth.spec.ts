import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { Auth } from './auth';

describe('Auth', () => {
  let component: Auth;
  let fixture: ComponentFixture<Auth>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        Auth,
        HttpClientTestingModule,
        RouterTestingModule,
        ReactiveFormsModule
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(Auth);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start on sign in form', () => {
    expect(component.isSignIn).toBeTrue();
    expect(component.formType).toBe('signIn');
  });

  it('should switch to sign up', () => {
    component.switchToSignUp();
    expect(component.isSignIn).toBeFalse();
    expect(component.formType).toBe('signUp');
  });

  it('should switch back to sign in', () => {
    component.switchToSignUp();
    component.switchToSignIn();
    expect(component.isSignIn).toBeTrue();
    expect(component.formType).toBe('signIn');
  });

  it('sign in form should have email and password controls', () => {
    expect(component.emailControl).toBeTruthy();
    expect(component.passwordControl).toBeTruthy();
  });

  it('sign up form should have name control', () => {
    component.switchToSignUp();
    expect(component.nameControl).toBeTruthy();
  });

  it('should return password strength object', () => {
    component.authForm.patchValue({ password: 'Test@1234' });
    const strength = component.getPasswordStrength();
    expect(strength.label).toBeTruthy();
    expect(strength.width).toBeTruthy();
    expect(strength.color).toBeTruthy();
  });

  it('should mark form touched on invalid submit', () => {
    component.onSubmit();
    expect(component.errorMessage).toBeTruthy();
  });

  it('should reset state on switch', () => {
    component.errorMessage = 'Some error';
    component.switchToSignUp();
    expect(component.errorMessage).toBe('');
  });
});