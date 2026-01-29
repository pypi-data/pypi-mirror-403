import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Add mock evaluations for development
if (import.meta.env.DEV && !window.__VOICEGROUND_EVALUATIONS__) {
  window.__VOICEGROUND_EVALUATIONS__ = [
    {
      name: "goal_achievement",
      type: "boolean",
      passed: true,
      reasoning: "The bot successfully helped the user complete their goal of making a reservation."
    },
    {
      name: "intent_classification",
      type: "category",
      category: "reserve a table",
      reasoning: "The user clearly expressed their intent to make a reservation for 2 people at 7pm."
    },
    {
      name: "bot_politeness",
      type: "rating",
      rating: 5,
      reasoning: "The bot was consistently polite, using courteous language and maintaining a professional tone throughout the conversation."
    }
  ];
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
