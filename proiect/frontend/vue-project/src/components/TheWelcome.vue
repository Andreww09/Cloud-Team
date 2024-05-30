<template>
  <div class="container">
    <header>
      <h1 class="title">Product Search</h1>
      <div v-if="user" class="user-info">
        <p>Logged in as: {{ user.email }}</p>
        <button @click="logout" class="logout-btn">Logout</button>
      </div>
      <div v-else>
        <button @click="login" class="login-btn">Login with Google</button>
      </div>
    </header>
    <main>
      <div v-if="!user" class="registration-form">
        <h2>Register</h2>
        <input v-model="email" type="email" placeholder="Email" class="input-field" />
        <input v-model="password" type="password" placeholder="Password" class="input-field" />
        <button @click="register" class="register-btn">Register</button>
      </div>
      <section class="search-section">
        <h2 style="color: #333;">Search by Keyword</h2>
        <div class="search-form">
          <input v-model="keyword" placeholder="Enter keyword" />
          <select v-model="order" style="color: #333;">
            <option value="ascending">Ascending</option>
            <option value="descending">Descending</option>
          </select>
          <input v-model="minPrice" type="number" placeholder="Min price" style="color: #333;" />
          <input v-model="maxPrice" type="number" placeholder="Max price" style="color: #333;" />
          <button @click="searchByKeyword" style="background-color: #007bff; color: white;">Search</button>
        </div>
        <div v-if="products.length > 0" class="results">
          <h3 style="color: #333;">Search Results</h3>
          <ul>
            <li v-for="product in products" :key="product.asin" @click="handleProductClickAndUpdateView(product.asin)">
              <img :src="product.image" alt="Product Image" />
              <div class="product-info">
                <p style="color: #333;">{{ product.desciption }}</p>
                <p style="color: #333;">Price: ${{ product.price }}</p>
              </div>
            </li>
          </ul>
        </div>
      </section>

      <section class="search-section">
        <h2 style="color: #333;">Search by URL</h2>
        <div class="search-form">
          <input v-model="productURL" placeholder="Enter product URL" style="color: #333;" />
          <select v-model="sortedBy" style="color: #333;">
            <option value="price">Price</option>
            <option value="sellerRating">Seller Rating</option>
          </select>
          <select v-model="order" style="color: #333;">
            <option value="ascending">Ascending</option>
            <option value="descending">Descending</option>
          </select>
          <input v-model="minPrice" type="number" placeholder="Min price" style="color: #333;" />
          <input v-model="maxPrice" type="number" placeholder="Max price" style="color: #333;" />
          <button @click="searchByURL" style="background-color: #007bff; color: white;">Search</button>
        </div>
        <div v-if="sellerPrices.length > 0" class="results">
          <h3 style="color: #333;">Search Results</h3>
          <ul>
            <li v-for="sellerPrice in sellerPrices" :key="sellerPrice.sellerId">
              <p style="color: #333;">Seller: {{ sellerPrice.sellerName }}</p>
              <p style="color: #333;">Price: ${{ sellerPrice.price }}</p>
              <p style="color: #333;">Rating: ${{ sellerPrice.sellerRating }}/5</p>
            </li>
          </ul>
        </div>
      </section>

      <section class="search-section">
        <h2 style="color: #333;">Search by Product Name</h2>
        <div class="search-form">
          <input v-model="productName" placeholder="Enter product name" style="color: #333;" />
          <button @click="searchByName" style="background-color: #007bff; color: white;">Search</button>
        </div>
        <div v-if="lowestPriceProduct" class="product-details">
          <h3 style="color: #333;">Product Details</h3>
          <img :src="lowestPriceProduct.image" alt="Product Image" />
          <p style="color: #333;">{{ lowestPriceProduct.desciption }}</p>
        </div>
        <div v-if="lowestPriceProvider" class="provider-details">
          <h3 style="color: #333;">Lowest Price Provider</h3>
          <p style="color: #333;">Seller: {{ lowestPriceProvider.sellerName }}</p>
          <p style="color: #333;">Price: ${{ lowestPriceProvider.price }}</p>
        </div>
      </section>

    <section v-if="additionalProductInfo.rating || additionalProductInfo.reviews.length > 0" class="search-section">
      <h2 style="color: #333;">Additional Product Information</h2>
      <div class="additional-info">
        <div v-if="additionalProductInfo.rating" class="rating-info">
          <h3 style="color: #333;">Rating</h3>
          <p style="color: #333;">{{ additionalProductInfo.rating }}/5</p>
          <h3 style="color: #333;">Overall score</h3>
          <p style="color: #333;">{{ additionalProductInfo.score }}</p>
        </div>
        <div v-if="additionalProductInfo.reviews.length > 0" class="reviews-info">
          <h3 style="color: #333;">Reviews</h3>
          <ul>
            <li v-for="(review, index) in additionalProductInfo.reviews" :key="index">
              <p style="color: #333;">{{ review.sentence }}</p>
              <p style="color: #333;">Sentiment: {{ review.sentiment }}</p>
            </li>
          </ul>
        </div>
      </div>
    </section>

      <section class="search-section" v-if="user">
        <h2 style="color: #333;">Search History</h2>
          <div class="search-history">
            <ul>
              <li v-for="entry in searchHistory" :key="entry.timestamp">
                <p>{{ entry.search_term }}</p>
                <p>{{ entry.timestamp }}</p>
              </li>
            </ul>
          </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { auth, provider, signInWithPopup, createUserWithEmailAndPassword, signOut } from '../firebase.js'

// State management
const user = ref(null)
const email = ref('')
const password = ref('')
const keyword = ref('')
const productName = ref('')
const sortedBy = ref('price')
const order = ref('ascending')
const minPrice = ref('')
const maxPrice = ref('')
const products = ref([])
const lowestPriceProduct = ref(null)
const lowestPriceProvider = ref(null)
const searchHistory = ref([])
const additionalProductInfo = ref({ rating: null, reviews: [], score: null })
const sellerPrices = ref([])
const productURL = ref('')

// Listen for authentication state changes
auth.onAuthStateChanged((loggedInUser) => {
  user.value = loggedInUser
  if (loggedInUser) {
    // Fetch search history if user is logged in
    fetchSearchHistory(loggedInUser.uid)
  } else {
    // Clear search history if user logs out
    searchHistory.value = []
  }
})

// Fetch search history for the logged-in user
const fetchSearchHistory = async (userId) => {
  try {
    const response = await axios.get(`http://localhost:5000/get-history?uid=${userId}`)
    searchHistory.value = response.data
  } catch (error) {
    console.error('Error fetching search history:', error)
  }
}

// Login function using Google authentication provider
const login = async () => {
  try {
    const result = await signInWithPopup(auth, provider)
    user.value = result.user
  } catch (error) {
    console.error('Error logging in:', error)
  }
}

// Logout function
const logout = async () => {
  try {
    await signOut(auth)
    user.value = null
  } catch (error) {
    console.error('Error logging out:', error)
  }
}

// Registration function
const register = async () => {
  try {
    const result = await createUserWithEmailAndPassword(auth, email.value, password.value)
    user.value = result.user
  } catch (error) {
    console.error('Error registering user:', error)
  }
}

// Function to fetch additional product info by ASIN
const fetchAdditionalProductInfo = async (asin) => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/lookup-product', {
      params: {
        url: 'https://www.amazon.com/dp/${asin}'
      }
    })
    const { rating, reviews, score } = response.data
    additionalProductInfo.value = { rating, reviews, score }
  } catch (error) {
    console.error('Error fetching additional product info:', error)
    additionalProductInfo.value = { rating: null, reviews: [] }
  }
}


// Function to search products by keyword
const searchByKeyword = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/search-by-keyword', {
      params: {
        keyword: keyword.value,
        order: order.value,
        minPrice: minPrice.value,
        maxPrice: maxPrice.value,
        uid: user.value.uid
      }
    })
    products.value = response.data
    lowestPriceProduct.value = null
    lowestPriceProvider.value = null
  } catch (error) {
    console.error('Error searching products by keyword:', error)
  }
}

// Function to search for the lowest price offer by product name
const searchByName = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/search-by-keyword', {
      params: {
        keyword: productName.value,
        uid: user.value.uid
      }
    })
    const searchResults = response.data
    if (searchResults.length > 0) {
      lowestPriceProduct.value = searchResults[0]
      await searchLowestPriceByAsin(lowestPriceProduct.value.asin)
      await fetchAdditionalProductInfo(lowestPriceProduct.value.asin)
    } else {
      lowestPriceProduct.value = null
      lowestPriceProvider.value = null
    }
    products.value = []
  } catch (error) {
    console.error('Error fetching product by name:', error)
  }
}

// Function to search for the lowest price offer by ASIN
const searchLowestPriceByAsin = async (asin) => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/lookup-seller-prices', {
      params: {
        url: `https://www.amazon.com/dp/${asin}`,
        sortedBy: 'price',
        order: 'ascending',
        uid: user.value.uid
      }
    })
    const offers = response.data
    if (offers.length > 0) {
      lowestPriceProvider.value = offers.sort((a, b) => a.price - b.price)[0]
    } else {
      lowestPriceProvider.value = null
    }
  } catch (error) {
    console.error('Error fetching product prices by ASIN:', error)
  }
}

// Function to handle product click and update view
const handleProductClickAndUpdateView = async (asin) => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/search-by-keyword', {
      params: {
        keyword: asin,
        uid: user.value.uid
      }
    })
    const productDetails = response.data
    if (productDetails.length > 0) {
      products.value = [productDetails[0]]; // Set products to an array containing only the clicked product
      lowestPriceProduct.value = productDetails[0];
      await searchLowestPriceByAsin(asin);
      await fetchAdditionalProductInfo(asin);
      // Clear lowestPriceProduct and lowestPriceProvider values
      lowestPriceProduct.value = null;
      lowestPriceProvider.value = null;
    } else {
      lowestPriceProduct.value = null;
      lowestPriceProvider.value = null;
    }
    productName.value = ""; // Clear productName
  } catch (error) {
    console.error('Error handling product click and updating view:', error)
  }
}

const searchByURL = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/lookup-seller-prices', {
      params: {
        url: productURL.value,
        sortedBy: sortedBy.value,
        order: order.value,
        minPrice: minPrice.value,
        maxPrice: maxPrice.value,
        uid: user.value.uid
      }
    })
    const index = productURL.value.indexOf("dp/") + "dp/".length;
    const substring = productURL.value.substring(index);
    await fetchAdditionalProductInfo(substring)
    sellerPrices.value = response.data
  } catch (error) {
    console.error('Error searching by URL:', error)
  }
}

</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

header {
  text-align: center;
  margin-bottom: 20px;
}

h1 {
  font-size: 2rem;
  color: '#333';
}

.user-info p {
  margin-bottom: 10px;
}

.login-btn,
.logout-btn,
.register-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  color: white;
}

.login-btn {
  background-color: #007bff;
}

.logout-btn {
  background-color: #dc3545;
}

.register-btn {
  background-color: #007bff;
}

.input-field {
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  margin-bottom: 10px;
  width: 100%;
}

.registration-form {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.registration-form h2 {
  margin-bottom: 10px;
}

.registration-form button {
  width: 100%;
}

main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-section {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search-form input,
.search-form select,
.search-form button {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.search-form button {
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}

.search-form button:hover {
  background-color: #0056b3;
}

.additional-info {
  margin-top: 20px;
}

.rating-info,
.reviews-info {
  margin-bottom: 20px;
}

.rating-info h3,
.reviews-info h3 {
  color: #333;
  margin-bottom: 10px;
}

.reviews-info ul {
  list-style: none;
  padding: 0;
}

.reviews-info li {
  margin-bottom: 10px;
}

.results ul {
  list-style: none;
  padding: 0;
}

.results li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.results li:hover {
  background-color: #f0f0f0;
}

.results img {
  width: 50px;
  height: 50px;
  object-fit: cover;
  border-radius: 4px;
}

.product-info {
  flex-grow: 1;
}

.product-details img,
.provider-details img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 4px;
}

/* Color adjustments for text */
h1, h2, h3, p, input, select {
  color: #333;
}

.title{
  color: #e5e1e1;
}
</style>