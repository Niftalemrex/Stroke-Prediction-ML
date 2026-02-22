// Splash.tsx
import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import './splash.css'

interface SplashProps {
  delay?: number
  onLoadStart?: () => void
}

const Splash = ({ delay = 5700, onLoadStart }: SplashProps) => {
  const navigate = useNavigate()
  const [progress, setProgress] = useState(0)
  const [isVisible, setIsVisible] = useState(true)
  const animationRef = useRef<number | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    console.log('Splash screen mounted, delay:', delay)
    onLoadStart?.()
    const startTime = Date.now()

    // Animate progress
    const animate = () => {
      const elapsed = Date.now() - startTime
      const percentage = Math.min((elapsed / delay) * 100, 100)
      setProgress(percentage)

      if (elapsed < delay) {
        animationRef.current = requestAnimationFrame(animate)
      }
    }

    animationRef.current = requestAnimationFrame(animate)

    // Set navigation timeout
    timeoutRef.current = setTimeout(() => {
      console.log('Splash complete, navigating to intro')
      setIsVisible(false)
      setTimeout(() => {
        navigate('/stroke-intro')
      }, 300)
    }, delay)

    return () => {
      console.log('Splash screen cleanup')
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [navigate, delay, onLoadStart])

  return (
    <div 
      className={`splash-container ${!isVisible ? 'splash-exit' : ''}`}
      aria-label="Loading StrokePredict application"
      role="status"
    >
      {/* Background Elements */}
      <div className="splash-background-orbs">
        <div className="splash-orb" style={{ left: '20%', animationDelay: '0s', background: 'radial-gradient(circle at 30% 30%, rgba(59, 130, 246, 0.15) 0%, transparent 70%)' }} />
        <div className="splash-orb" style={{ left: '50%', animationDelay: '0.5s', background: 'radial-gradient(circle at 30% 30%, rgba(139, 92, 246, 0.15) 0%, transparent 70%)' }} />
        <div className="splash-orb" style={{ left: '80%', animationDelay: '1s', background: 'radial-gradient(circle at 30% 30%, rgba(59, 130, 246, 0.15) 0%, transparent 70%)' }} />
      </div>

      {/* App Icon */}
      <div className="splash-icon-wrapper">
        <div className="splash-icon-inner" aria-hidden="true">
          🧠
        </div>
        <div className="splash-icon-glow" />
      </div>

      {/* App Name */}
      <h1 className="splash-title">
        StrokePredict
        <span className="splash-title-gradient" />
      </h1>

      {/* Tagline */}
      <p className="splash-subtitle">
        Clinical risk analysis
        <span className="splash-dots">
          <span className="splash-dot">.</span>
          <span className="splash-dot">.</span>
          <span className="splash-dot">.</span>
        </span>
      </p>

      {/* Progress bar */}
      <div className="splash-progress-container">
        <div 
          className="splash-progress-bar"
          style={{ width: `${progress}%` }}
        />
        <div className="splash-progress-text">
          {Math.round(progress)}%
        </div>
      </div>

      {/* Loader */}
      <div className="splash-loader-wrapper">
        <div className="splash-loader" />
        <div className="splash-loader-ring" />
      </div>

      {/* Loading message */}
      <p className="splash-loading-message">
        Initializing neural network models...
      </p>

      {/* Version info */}
      <div className="splash-version-info">
        <span className="splash-version">v2.1.0</span>
        <span className="splash-badge">BETA</span>
      </div>
    </div>
  )
}

export default Splash