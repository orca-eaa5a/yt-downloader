
// import HelloWorld from '@/components/HelloWorld'
import Main from '@/pages/Main'

import { createRouter, createMemoryHistory } from 'vue-router';
const routes = [
  {
    path: '/',
    name: 'Main',
    component: Main
  }
]

const router = new createRouter({
  history: createMemoryHistory(),
  routes: routes
});

export default router;