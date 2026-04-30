import { pill } from '../tokens'

export function Pill({ type, label }) {
  return <span style={pill(type, label)}>{label ?? type}</span>
}