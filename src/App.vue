<template>
  <div id="app">
    <h1>Navy Dashboard</h1>
    <HomeView />
  </div>
</template>

<script>
import HomeView from "./views/Home.vue";

export default {
  name: "App",
  components: {
    HomeView,
  },
};
</script>

<style>
#app {
  text-align: center;
  font-family: Arial, sans-serif;
}
</style>
