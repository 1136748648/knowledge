import request from './request'

export const askQuestion = (question) => request.post('/qa/ask', { question })
