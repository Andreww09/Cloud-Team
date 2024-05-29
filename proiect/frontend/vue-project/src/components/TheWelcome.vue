<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { auth, provider, signInWithPopup, signOut } from '../firebase'
import WelcomeItem from './WelcomeItem.vue'
import DocumentationIcon from './icons/IconDocumentation.vue'
import CommunityIcon from './icons/IconCommunity.vue'

// State management
const keyword = ref('')
const productName = ref('')
const sortedBy = ref('price')
const order = ref('ascending')
const minPrice = ref('')
const maxPrice = ref('')
const products = ref([])
const lowestPriceProvider = ref(null)
const searchHistory = ref([])
const user = ref(null)
const token = ref(null)

// Function to search products by keyword
const searchByKeyword = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/search-by-keyword', {
      params: {
        keyword: keyword.value,
        sortedBy: sortedBy.value,
        order: order.value,
        minPrice: minPrice.value,
        maxPrice: maxPrice.value
      },
      headers: { Authorization: `Bearer ${token.value}` }
    })
    products.value = response.data
  } catch (error) {
    console.error('Error searching products by keyword:', error)
  }
}

// Function to search for the lowest price offer by product name
const searchByName = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/lookup-seller-prices', {
      params: {
        url: productName.value,
        sortedBy: 'price',
        order: 'ascending'
      },
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

// Function to search for the lowest price offer by ASIN
const searchLowestPriceByAsin = async (asin) => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/lookup-seller-prices', {
      params: {
        url: `https://www.amazon.com/dp/${asin}`,
        sortedBy: 'price',
        order: 'ascending'
      },
      headers: { Authorization: `Bearer ${token.value}` }
    })
    const offers = response.data
    if (offers.length > 0) {
      lowestPriceProvider.value = offers.sort((a, b) => a.price - b.price)[0]
    }
  } catch (error) {
    console.error('Error fetching product prices by ASIN:', error)
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
    const response = await axios.get('http://127.0.0.1:5000/search-history', {
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
      <template #heading>Search by Keyword</template>
      <input v-model="keyword" placeholder="Enter keyword" />
      <select v-model="sortedBy">
        <option value="price">Price</option>
        <option value="rating">Rating</option>
      </select>
      <select v-model="order">
        <option value="ascending">Ascending</option>
        <option value="descending">Descending</option>
      </select>
      <input v-model="minPrice" type="number" placeholder="Min price" />
      <input v-model="maxPrice" type="number" placeholder="Max price" />
      <button @click="searchByKeyword">Search</button>
      <div v-if="products.length > 0">
        <h3>Search Results</h3>
        <ul>
          <li v-for="product in products" :key="product.asin" @click="searchLowestPriceByAsin(product.asin)">
            <img :src="product.image" alt="Product Image" />
            <p>{{ product.description }}</p>
            <p>Price: ${{ product.price }}</p>
          </li>
        </ul>
      </div>
    </WelcomeItem>

    <WelcomeItem>
      <template #icon>
        <CommunityIcon />
      </template>
      <template #heading>Search by Product Name</template>
      <input v-model="productName" placeholder="Enter product name" />
      <input v-model="minPrice" type="number" placeholder="Min price" />
      <input v-model="maxPrice" type="number" placeholder="Max price" />
      <button @click="searchByName">Search</button>
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
