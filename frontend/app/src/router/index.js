
// import HelloWorld from '@/components/HelloWorld'
import Main from '@/pages/Main';

import { createRouter, createWebHistory } from 'vue-router';
const routes = [
  {
    path: '/',
    name: 'Main',
    component: Main
  }
]

const router = new createRouter({
  history: createWebHistory(),
  routes: routes
});

export default router;