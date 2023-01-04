// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
// import Vue from 'vue'
// import App from './App'
// import router from './router'

// Vue.config.productionTip = false


// new Vue({
//   el: '#app',
//   router,
//   components: { App },
//   template: '<App/>'
// })

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import PrimeVue from 'primevue/config';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import SplitButton from 'primevue/splitbutton';
import InputMask from 'primevue/inputmask';
import Button from 'primevue/button';

import "primevue/resources/themes/md-light-deeppurple/theme.css"; //theme
import "primevue/resources/primevue.min.css"; //core CSS
import "primeicons/primeicons.css"; //icons
import "primeflex/primeflex.css";

// import BootstrapVue3 from 'bootstrap-vue-3';
// import 'bootstrap/dist/css/bootstrap.css'
// import 'bootstrap-vue-3/dist/bootstrap-vue-3.css'

const app = createApp(App);
app.use(router);
// app.use(BootstrapVue3)
app.use(PrimeVue, {ripple:true});
app.mount('#app');

app.component('Dialog', Dialog);
app.component('InputText', InputText);
app.component('InputMask', InputMask);
app.component('SplitButton', SplitButton);
app.component('Button', Button);

