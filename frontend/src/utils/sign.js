import CryptoJS from 'crypto-js'
import { logger } from './logger'

const LARGE_FIELD_THRESHOLD = 1000

export function generateNonce(length = 16) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

export function normalizeString(value) {
  if (typeof value !== 'string') return value
  
  let normalized = value.replace(/\r\n/g, '\n')
  normalized = normalized.trim()
  normalized = normalized.replace(/\n{3,}/g, '\n\n')
  normalized = normalized.replace(/[ \t]+/g, ' ')
  
  return normalized
}

export function sha256Hash(value) {
  return CryptoJS.SHA256(value).toString(CryptoJS.enc.Hex)
}

export function computeBodyHash(bodyString) {
  if (!bodyString) {
    bodyString = ''
  }
  return CryptoJS.SHA256(bodyString).toString(CryptoJS.enc.Hex)
}

export function generateSignature(params, secret) {
  if (!params) {
    params = {}
  }
  
  const processedParams = {}
  
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === 'string') {
      processedParams[key] = value.trim()
    } else if (typeof value === 'object' && value !== null) {
      processedParams[key] = JSON.stringify(value)
    } else {
      processedParams[key] = String(value)
    }
  }
  
  const sortedKeys = Object.keys(processedParams).sort()
  const signString = sortedKeys.map(key => {
    return `${key}=${encodeURIComponent(processedParams[key])}`
  }).join('&')
  
  logger.debug(`签名前字符串 ${signString}`)
  return CryptoJS.HmacSHA256(signString, secret).toString(CryptoJS.enc.Hex)
}

export function signRequest(config, secret) {
  if (!secret) {
    return config
  }
  
  const timestamp = Math.floor(Date.now() / 1000).toString()
  const nonce = generateNonce()
  
  let bodyString = ''
  if (config.data) {
    if (typeof config.data === 'string') {
      bodyString = config.data
    } else if (typeof config.data === 'object') {
      bodyString = JSON.stringify(config.data)
    }
  }
  
  const bodyHash = computeBodyHash(bodyString)
  logger.debug(`Request body hash: ${bodyHash}`)
  
  const signParams = {
    timestamp,
    nonce,
    body_hash: bodyHash
  }
  const signature = generateSignature(signParams, secret)
  
  if (!config.headers) {
    config.headers = {}
  }
  
  config.headers['X-Sign-Timestamp'] = timestamp
  config.headers['X-Sign-Nonce'] = nonce
  config.headers['X-Sign-Signature'] = signature
  
  return config
}