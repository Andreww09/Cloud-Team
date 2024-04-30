<template>
  <div>
    <h1>PDF Upload and Screening</h1>
    <!-- Show login button if user is not authenticated -->
    <button v-if="!isAuthenticated" @click="login">Login with Azure AD</button>
    <div v-else>
      <input type="file" @change="handleFileUpload" v-if="isAuthenticated">
      <button @click="uploadFile" v-if="isAuthenticated">Upload PDF</button>
      <div v-if="screeningResult && isAuthenticated">
        <p>{{ screeningResult }}</p>
        <button v-if="isContentSafe" @click="readContent">Read Content</button>
        <p v-else>The content is deemed unsafe and cannot be read out loud.</p>
      </div>
      <div v-if="pdfContent && isAuthenticated">
        <h2>Uploaded PDF Content:</h2>
        <pre>{{ filename }}</pre>
        <pre>{{ pdfContent }}</pre>
      </div>
      <h2>Previously Uploaded Files:</h2>
      <ul>
        <!-- Loop through uploadedFiles and display filenames as clickable links -->
        <li v-for="file in uploadedFiles" :key="file.name">
          <a href="#" @click="readUploadedContent(file.name)">{{ file.name }}</a>
        </li>
      </ul>
      <button v-if="isAuthenticated" @click="logout">Logout</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'; // for making HTTP requests

export default {
  data() {
    return {
      isAuthenticated: false, // Track user authentication status
      user: null, // Store user information
      file: null,
      screeningResult: null,
      isContentSafe: false,
      pdfContent: null, // to store the content of the uploaded PDF
      filename: null, // to store the name of the uploaded PDF
      uploadedFiles: [] // to store previously uploaded files
    };
  },
  mounted() {
    // Check authentication status when the component is mounted
    this.checkAuthentication();
  },
  methods: {
    login() {
      try {
        const loginUrl = 'https://readerlogin.b2clogin.com/readerlogin.onmicrosoft.com/oauth2/v2.0/authorize?p=B2C_1_signupsignintest2&client_id=7ae0133c-788a-4466-883f-cc089edc8ab4&nonce=defaultNonce&redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Fredirected&scope=openid&response_type=id_token&prompt=login';
        window.location.href = loginUrl;
      } catch (error) {
        console.error('Error during authentication:', error);
      }
    },
    async checkAuthentication() {
      try {
        // Call an API endpoint on the Flask backend to check authentication status
        const response = await axios.get('http://localhost:5000/check-authentication');

        // Set isAuthenticated based on the response from the backend
        this.isAuthenticated = response.data.isAuthenticated;
        this.user = response.data.user;
      } catch (error) {
        console.error('Error checking authentication status:', error);
      }
    },
    async logout() {
      try {
        // Call an API endpoint on the Flask backend to log out
        await axios.post('http://localhost:5000/logout');

        // After logging out, set isAuthenticated to false and clear user data
        this.isAuthenticated = false;
        this.user = null;
      } catch (error) {
        console.error('Error logging out:', error);
      }
    },
    handleFileUpload(event) {
      this.file = event.target.files[0];
    },
    async uploadFile() {
      try {
        // Check if the file is safe using Azure AI Content Safety service
        const formData = new FormData();
        formData.append('file', this.file);

        // Make HTTP POST request to Azure AI Content Safety service
        const safetyCheckResponse = await axios.post('http://localhost:5000/check-content-safety', formData);

        // Check the response from the safety check
        if (safetyCheckResponse.data.isSafe) {
          // If the file is safe, proceed with uploading it to the backend
          await axios.post('http://localhost:5000/upload', formData);
        } else {
          // If the file is deemed unsafe, set the screeningResult accordingly
          this.screeningResult = 'The content is deemed unsafe and cannot be read out loud.';
        }
        this.isContentSafe = safetyCheckResponse.data.isSafe;
      } catch (error) {
        console.error('Error uploading file:', error);
      }
    },
    async readContent() {
      try {
        // Get the content of the uploaded PDF file
        const filename = this.file.name;
        this.uploadedFiles.push(filename);
        const fileContentResponse = await axios.get(`http://localhost:5000/file/${filename}`);

        // Store the content in pdfContent
        this.pdfContent = fileContentResponse.data;

        // Get the access token and subdomain for Azure AI Immersive Reader
        const response = await axios.get('http://localhost:5000/GetTokenAndSubdomain');
        const auth_token = response.data.token;
        const subdomain = response.data.subdomain;

        // Use Azure AI Immersive Reader SDK to read content
        ImmersiveReader.launchReader({
          authToken: auth_token,
          content: this.pdfContent, // Pass the content of the PDF file
          subdomain: subdomain,
          locale: 'en-us'
        });
      } catch (error) {
        console.error('Error reading content:', error);
      }
    },
    async readUploadedContent(filename) {
      try {
        // Fetch content of previously uploaded PDF file
        const fileContentResponse = await axios.get(`http://localhost:5000/file/${filename}`);

        // Use Azure AI Immersive Reader SDK to read content
        const response = await axios.get('http://localhost:5000/GetTokenAndSubdomain');
        const auth_token = response.data.token;
        const subdomain = response.data.subdomain;

        // Use Azure AI Immersive Reader SDK to read content
        ImmersiveReader.launchReader({
          authToken: auth_token,
          content: fileContentResponse.data, // Pass the content of the PDF file
          subdomain: subdomain,
          locale: 'en-us'
        });
      } catch (error) {
        console.error('Error reading content:', error);
      }
    }
  }
}
</script>
