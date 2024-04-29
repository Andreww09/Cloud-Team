<template>
  <div>
    <h1>PDF Upload and Screening</h1>
    <input type="file" @change="handleFileUpload">
    <button @click="uploadFile">Upload PDF</button>
    <div v-if="screeningResult">
      <p>{{ screeningResult }}</p>
      <button v-if="isContentSafe" @click="readContent">Read Content</button>
      <p v-else>The content is deemed unsafe and cannot be read out loud.</p>
    </div>
    <div v-if="pdfContent">
      <h2>Uploaded PDF Content:</h2>
      <pre>{{ pdfContent }}</pre>
    </div>
  </div>
</template>

<script>
import axios from 'axios'; // for making HTTP requests

export default {
  data() {
    return {
      file: null,
      screeningResult: null,
      isContentSafe: false,
      pdfContent: null // to store the content of the uploaded PDF
    };
  },
  methods: {
    handleFileUpload(event) {
      this.file = event.target.files[0];
    },
    async uploadFile() {
      try {
        const formData = new FormData();
        formData.append('file', this.file);

        // Make HTTP POST request to Flask backend
        const response = await axios.post('http://localhost:5000/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        // Process response and set screeningResult and isContentSafe
        this.screeningResult = response.data.result;
        this.isContentSafe = true //response.data.isSafe;

        // Set pdfContent to null when a new file is uploaded
        this.pdfContent = null;
      } catch (error) {
        console.error('Error uploading file:', error);
        this.screeningResult = 'Error uploading file';
        this.isContentSafe = true //false;
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
  }
}
</script>
