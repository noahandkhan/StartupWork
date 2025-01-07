<template>
    <div class="home">
      <div class="prompt-section">
        <h2>Enter a Query</h2>
        <input
          v-model="userPrompt"
          type="text"
          placeholder="e.g., List underperforming suppliers"
        />
        <button @click="fetchData">Submit</button>
      </div>
  
      <div v-if="loading">Loading...</div>
  
      <div v-if="error" class="error">{{ error }}</div>
  
      <DataGrid v-if="results.length" :data="results" />
    </div>
  </template>
  
  <script>
  import DataGrid from "../components/DataGrid.vue";
  
  export default {
    name: "HomeView", // Updated name
    components: {
      DataGrid,
    },
    data() {
      return {
        userPrompt: "",
        results: [],
        loading: false,
        error: null,
      };
    },
    methods: {
      async fetchData() {
        if (!this.userPrompt.trim()) {
          this.error = "Please enter a query.";
          return;
        }
        this.loading = true;
        this.error = null;
        this.results = [];
  
        try {
          const response = await fetch("http://127.0.0.1:5000/query", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ query: this.userPrompt }),
          });
  
          if (!response.ok) {
            throw new Error("Failed to fetch data from the server.");
          }
  
          const data = await response.json();
          this.results = data;
        } catch (err) {
          this.error = err.message || "Something went wrong.";
        } finally {
          this.loading = false;
        }
      },
    },
  };
  </script>
  
  <style scoped>
  .prompt-section {
    margin: 20px;
  }
  input {
    padding: 10px;
    margin-right: 10px;
  }
  button {
    padding: 10px 15px;
    background-color: #007bff;
    color: white;
    border: none;
    cursor: pointer;
  }
  button:hover {
    background-color: #0056b3;
  }
  .error {
    color: red;
  }
  </style>
  