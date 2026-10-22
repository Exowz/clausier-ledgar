import deck from './generated/deck.json'
import cloud from './generated/cloud.json'

export { deck, cloud }

export const integer = (value: number) => Math.round(value).toLocaleString('en-US')
export const f1 = (value: number) => value.toFixed(3)
export const percent = (value: number) => `${Math.round(value * 100)}%`
export const compactTime = (seconds: number) => seconds < 60
  ? `${seconds.toFixed(1)} s`
  : `${Math.floor(seconds / 60)} min ${Math.round(seconds % 60)} s`

export const tfidf = deck.results_table.find(row => row.model === 'TF-IDF + logistic regression')!
export const legalBert = deck.results_table.find(row => row.model === 'Legal-BERT (up to 10 epochs)')!
