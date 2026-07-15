import axios from 'axios'

const api = axios.create({
    baseURL: 'http://localhost:8000',
})

// automatically attach token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// On a 401, try to refresh the access token once and retry the original
// request. Only if the refresh itself fails do we clear the session and send
// the user back to the login page. Token endpoints are excluded so a wrong
// password or a dead refresh token can't loop.
let refreshPromise = null

function refreshAccessToken() {
    // Share one in-flight refresh between concurrent 401s.
    if (!refreshPromise) {
        refreshPromise = axios
            .post('http://localhost:8000/api/token/refresh/', {
                refresh: localStorage.getItem('refresh_token'),
            })
            .then((response) => {
                localStorage.setItem('access_token', response.data.access)
                // With ROTATE_REFRESH_TOKENS the backend also returns a new
                // refresh token and blacklists the old one — store it or the
                // NEXT refresh would fail with a blacklisted token.
                if (response.data.refresh) {
                    localStorage.setItem('refresh_token', response.data.refresh)
                }
                return response.data.access
            })
            .finally(() => {
                refreshPromise = null
            })
    }
    return refreshPromise
}

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config
        const isTokenEndpoint = original?.url?.includes('/api/token/')
        const hasRefreshToken = Boolean(localStorage.getItem('refresh_token'))

        if (
            error.response?.status === 401 &&
            !original._retried &&
            !isTokenEndpoint &&
            hasRefreshToken
        ) {
            original._retried = true
            try {
                const newAccess = await refreshAccessToken()
                original.headers.Authorization = `Bearer ${newAccess}`
                return api(original)
            } catch (refreshError) {
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
                localStorage.removeItem('username')
                window.location.assign('/login')
            }
        }

        return Promise.reject(error)
    },
)

export default api
