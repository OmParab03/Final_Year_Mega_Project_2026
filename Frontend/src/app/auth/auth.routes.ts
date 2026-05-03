import { Routes } from '@angular/router';
import { Auth } from './auth';
import { Dashboard } from '../dashboard/dashboard';

export const authRoutes: Routes = [
  { 
    path: '', 
    component: Auth 
  },
  { 
    path: 'dashboard', 
    component: Dashboard 
  }
];