import CryptoJS from 'crypto-js'

export function generateNonce(length = 16) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

export function generateSignature(params, secret) {
  if (!params) {
    params = {}
  }
  
  const sortedKeys = Object.keys(params).sort()
  const signString = sortedKeys.map(key => {
    const value = params[key]
    const stringValue = typeof value === 'object' ? JSON.stringify(value) : value
    return `${key}=${stringValue}`
  }).join('&')
  console.log(`签名前字符串 ${signString}`);
  return CryptoJS.HmacSHA256(signString, secret).toString(CryptoJS.enc.Hex)
}

export function signRequest(config, secret) {
  if (!secret) {
    return config
  }
  
  const timestamp = Math.floor(Date.now() / 1000).toString()
  const nonce = generateNonce()
  
  const params = {}
  
  if (config.params) {
    Object.assign(params, config.params)
  }
  
  if (config.data && typeof config.data === 'object') {
    Object.assign(params, config.data)
  }
  
  const signParams = { ...params, timestamp, nonce }
  const signature = generateSignature(signParams, secret)
  
  if (!config.headers) {
    config.headers = {}
  }
  
  config.headers['X-Sign-Timestamp'] = timestamp
  config.headers['X-Sign-Nonce'] = nonce
  config.headers['X-Sign-Signature'] = signature
  
  return config
}
