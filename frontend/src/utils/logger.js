const isDev = import.meta.env.DEV

export const logger = {
  debug: (...args) => {
    if (isDev) {
      console.debug(...args)
    }
  },
  log: (...args) => {
    console.log(...args)
  },
  info: (...args) => {
    console.info(...args)
  },
  warn: (...args) => {
    console.warn(...args)
  },
  error: (...args) => {
    console.error(...args)
  }
}

export default logger