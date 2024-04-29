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
  </div>
</template>

<script>
import axios from 'axios'; // for making HTTP requests

export default {
  data() {
    return {
      file: null,
      screeningResult: null,
      isContentSafe: false
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
        this.isContentSafe = response.data.isSafe;
      } catch (error) {
        console.error('Error uploading file:', error);
        this.screeningResult = 'Error uploading file';
        this.isContentSafe = false;
      }
    },
    async readContent() {
      // Get the URL for the PDF file from the backend
      const pdfUrlResponse = await axios.get('/get_pdf_url');
      const pdfUrl = pdfUrlResponse.data.pdfUrl;
      const response = await axios.get('/GetTokenAndSubdomain');
      const auth_token = response['token'];
      const subdomain = response['subdomain'];
      // Use Azure AI Immersive Reader SDK to read content
      ImmersiveReader.launchReader({
        authToken: auth_token,
        content: pdfUrl,
        subdomain: subdomain,
        locale: 'en-us'
      });
    }
  }
}
</script>
