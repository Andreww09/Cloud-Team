<template>
  <div>
    <h1>PDF Upload and Screening</h1>
    <!-- Show login button if user is not authenticated -->
    <button v-if="!isAuthenticated" @click="login">Login with Azure AD</button>
    <div v-else>
      <input type="file" @change="handleFileUpload">
      <button @click="uploadFile">Upload PDF</button>
      <div v-if="screeningResult">
        <p>{{ screeningResult }}</p>
        <button v-if="isContentSafe" @click="readContent">Read Content</button>
        <p v-else>The content is deemed unsafe and cannot be read out loud.</p>
      </div>
      <div v-if="pdfContent">
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
  methods: {
    async login() {
      try {
        // Configure MSAL.js with your Azure AD application details
        const config = {
          auth: {
            clientId: 'YOUR_CLIENT_ID',
            authority: 'https://login.microsoftonline.com/YOUR_TENANT_ID',
            redirectUri: 'http://localhost:8080' // Redirect URI configured in your Azure AD application
          }
        };

        const msalInstance = new Msal.UserAgentApplication(config);

        // Login using MSAL.js
        const loginResponse = await msalInstance.loginPopup();

        // Retrieve user information from the login response
        const user = msalInstance.getAccount();

        // Set isAuthenticated to true and store user information
        this.isAuthenticated = true;
        this.user = {
          username: user.username, // Example: user.displayName,
          email: user.email // Example: user.email
          // You may need to retrieve additional user data based on your application's requirements
        };
      } catch (error) {
        console.error('Error during authentication:', error);
      }
    },

    handleFileUpload(event) {
      this.file = event.target.files[0];
    },
    async uploadFile() {
      try {
        // Upload file to the backend
        const formData = new FormData();
        formData.append('file', this.file);

        // Make HTTP POST request to Flask backend to upload the file
        await axios.post('http://localhost:5000/upload', formData);

      } catch (error) {
        console.error('Error uploading file:', error);
      }
    },
    async readContent() {
      try {
        // Get the content of the uploaded PDF file
        const filename = this.file.name;
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
    }
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
