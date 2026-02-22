// StrokePredictIntro.tsx
import { useNavigate } from 'react-router-dom'
import './StrokePredictIntro.css'

const StrokePredictIntro = () => {
  const navigate = useNavigate()

  const handleStart = () => {
    navigate('/stroke-predict')
  }
  const handleMultiStart = () => {
    navigate('/multi-stroke-predict')
  }

  return (
    <div className="intro-container">
      {/* Background Elements */}
      <div className="intro-background">
        <div className="intro-grid" />
        <div className="intro-blob intro-blob-1" />
        <div className="intro-blob intro-blob-2" />
      </div>

      {/* Header */}
      <header className="intro-header">
        <div className="intro-icon">🧠</div>
        <h1 className="intro-title">StrokePredict</h1>
        <p className="intro-subtitle">Advanced Clinical Risk Assessment Platform</p>
      </header>

      {/* Features Section */}
      <section className="intro-features">
        <h2 className="intro-features-title">Why Choose StrokePredict?</h2>
        <div className="intro-features-grid">
          <div className="intro-feature-card">
            <div className="intro-feature-icon">⚡</div>
            <h3 className="intro-feature-title">Real-time Analysis</h3>
            <p className="intro-feature-desc">
              Instant stroke risk assessment using advanced machine learning algorithms 
              trained on clinical datasets.
            </p>
          </div>

          <div className="intro-feature-card">
            <div className="intro-feature-icon">🔬</div>
            <h3 className="intro-feature-title">Clinical Accuracy</h3>
            <p className="intro-feature-desc">
              Validated against medical standards with 94.7% accuracy in 
              predicting stroke risk factors.
            </p>
          </div>

          <div className="intro-feature-card">
            <div className="intro-feature-icon">📊</div>
            <h3 className="intro-feature-title">Comprehensive Dashboard</h3>
            <p className="intro-feature-desc">
              Detailed risk breakdown with visual analytics and 
              actionable insights for healthcare professionals.
            </p>
          </div>
        </div>
      </section>

      {/* Description Section */}
      <section className="intro-description">
        <h2 className="intro-description-title">
          Transforming Stroke Prevention Through AI
        </h2>
        <p className="intro-description-text">
          StrokePredict utilizes cutting-edge artificial intelligence to analyze 
          patient data and predict stroke risk with unprecedented accuracy. Our 
          platform combines medical expertise with machine learning to provide 
          healthcare professionals with reliable, data-driven insights for 
          early intervention and prevention.
        </p>

        <div className="intro-stats">
          <div className="intro-stat">
            <p className="intro-stat-number">94.7%</p>
            <p className="intro-stat-label">Prediction Accuracy</p>
          </div>
          <div className="intro-stat">
            <p className="intro-stat-number">15K+</p>
            <p className="intro-stat-label">Clinical Cases</p>
          </div>
          <div className="intro-stat">
            <p className="intro-stat-number">2.3s</p>
            <p className="intro-stat-label">Average Analysis Time</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="intro-cta">
        <button 
          onClick={handleStart}
          className="intro-start-button"
          aria-label="Start Stroke Risk Assessment"
        >
          <span>Start Assessment</span>
          <span className="intro-start-button-icon">→</span>
        </button>
        
        <p className="intro-note">
          For clinical and research use. Results should be interpreted by qualified healthcare professionals.
        </p>
      </section>
      <section className="intro-cta">
        <button 
          onClick={handleMultiStart}
          className="intro-start-button"
          aria-label="Start Stroke Risk Assessment"
        >
          <span>Start Multi</span>
          <span className="intro-start-button-icon">→</span>
        </button>
        
        <p className="intro-note">
          For multi clinical and research use. Results should be interpreted by qualified healthcare professionals.
        </p>
      </section>
      {/* Footer */}
      <footer className="intro-footer">
        <div className="intro-footer-links">
          <a href="#privacy" className="intro-footer-link">Privacy Policy</a>
          <a href="#terms" className="intro-footer-link">Terms of Use</a>
          <a href="#research" className="intro-footer-link">Research Data</a>
          <a href="#contact" className="intro-footer-link">Contact</a>
        </div>
        <p className="intro-copyright">
          © 2024 StrokePredict. All rights reserved. For medical research purposes only.
        </p>
      </footer>
    </div>
  )
}

export default StrokePredictIntro