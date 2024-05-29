<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { auth, provider, signInWithPopup, signOut } from '../firebase'
import WelcomeItem from './WelcomeItem.vue'
import DocumentationIcon from './icons/IconDocumentation.vue'
import CommunityIcon from './icons/IconCommunity.vue'

// State management
const productName = ref('')
const lowestPriceProvider = ref(null)
const searchHistory = ref([])
const user = ref(null)
const token = ref(null)

// Function to look up product prices
const lookUpProduct = async () => {
  try {
    const response = await axios.get(`http://localhost:5000/lookup-seller-prices`, {
      params: { url: `https://www.amazon.com/dp/${productName.value}` },
      headers: { Authorization: `Bearer ${token.value}` }
    })
    const offers = response.data
    if (offers.length > 0) {
      lowestPriceProvider.value = offers.sort((a, b) => a.price - b.price)[0]
    }
  } catch (error) {
    console.error('Error fetching product prices:', error)
  }
}

// Function to handle Google login
const handleGoogleLogin = async () => {
  try {
    const result = await signInWithPopup(auth, provider)
    user.value = result.user
    token.value = await user.value.getIdToken()
    fetchSearchHistory()
  } catch (error) {
    console.error('Error during Google login:', error)
  }
}

// Function to handle logout
const handleLogout = async () => {
  try {
    await signOut(auth)
    user.value = null
    token.value = null
    searchHistory.value = []
  } catch (error) {
    console.error('Error during logout:', error)
  }
}

// Fetch search history after login
const fetchSearchHistory = async () => {
  try {
    const response = await axios.get('http://localhost:5000/search-history', {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    searchHistory.value = response.data
  } catch (error) {
    console.error('Error fetching search history:', error)
  }
}

// Initialize Firebase Auth
auth.onAuthStateChanged(async (currentUser) => {
  if (currentUser) {
    user.value = currentUser
    token.value = await currentUser.getIdToken()
    fetchSearchHistory()
  } else {
    user.value = null
    token.value = null
    searchHistory.value = []
  }
})
</script>

<template>
  <div>
    <WelcomeItem>
      <template #icon>
        <DocumentationIcon />
      </template>
      <template #heading>Product Price Lookup</template>
      <input v-model="productName" placeholder="Enter product name or ASIN" />
      <button @click="lookUpProduct">Search</button>
      <div v-if="lowestPriceProvider">
        <p>Lowest Price Provider:</p>
        <p>Seller: {{ lowestPriceProvider.sellerName }}</p>
        <p>Price: ${{ lowestPriceProvider.price }}</p>
      </div>
    </WelcomeItem>

    <WelcomeItem>
      <template #icon>
        <CommunityIcon />
      </template>
      <template #heading>Login</template>
      <button v-if="!user" @click="handleGoogleLogin">Login with Google</button>
      <button v-if="user" @click="handleLogout">Logout</button>
      <div v-if="user">
        <p>Welcome, {{ user.displayName }}</p>
      </div>
      <div v-if="searchHistory.length > 0">
        <h3>Search History</h3>
        <ul>
          <li v-for="item in searchHistory" :key="item.id">{{ item.productName }}</li>
        </ul>
      </div>
    </WelcomeItem>
  </div>
</template>
